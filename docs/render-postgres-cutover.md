# Préparation de la connexion PostgreSQL sur Render

> **État : migration au démarrage implémentée, pas encore déployée.** Sur Render,
> l'application précontrôle les JSON, applique les migrations Alembic et audite
> les deux formats avant de servir les requêtes. Aucune migration de production
> n'a été lancée par la branche de travail.

## État vérifié au 18 octobre 2026

- Service web : `Calculateur-Moyennes`, région Frankfurt, branche de déploiement `web-app`, déploiement automatique activé.
- PostgreSQL : `Calculateur-Postgres`, PostgreSQL 18, même workspace et même région que le service.
- Base : `calculateur_postgres`.
- La base `Calculateur-Postgres` est disponible et contient la table legacy `anonymous_visitors`; les tables relationnelles `subjects` et `grades` ne sont pas encore présentes.
- Le précontrôle en lecture seule du 18 octobre a validé les **14 profils** présents : 10 matières, 28 notes et aucun profil invalide. Le contrôle a lu le JSON sans afficher ni modifier de données individuelles.
- Une copie SQLite temporaire, construite à partir des JSON actuels sans les identifiants de visiteurs, a passé les migrations `0001` et `0002`, puis l'audit : 14 profils, 10 matières, 28 notes dans les deux formats et aucun écart. Cette vérification ne couvre pas les particularités de PostgreSQL.
- Cette instance est la base primaire et aucune copie PostgreSQL n'est disponible dans le workspace Render. La restauration et la vérification sur une copie PostgreSQL restent à faire; aucune migration ni écriture n'a été lancée sur Render.
- Expiration indiquée pour l'offre gratuite : **16 novembre 2026**.
- L'accès réseau PostgreSQL comprend actuellement `0.0.0.0/0`. À revoir avant d'y stocker des données réelles.
- La révision `0001_relational_gradebook` crée les tables relationnelles et
  copie les données `anonymous_visitors.data` existantes. Le JSON reste la copie
  de secours et demeure synchronisé par l'application.
- Sur Render, `create_app()` exécute automatiquement le précontrôle, les
  migrations Alembic et l'audit avant que Gunicorn accepte les requêtes. Un
  verrou consultatif PostgreSQL évite que plusieurs workers migrent en même
  temps; la migration verrouille aussi la table legacy pendant la copie.
- Si un profil legacy ne passe pas la validation, le démarrage échoue avant les
  changements de schéma et les données JSON restent intactes. Si l'audit après
  migration échoue, la nouvelle version refuse de servir les requêtes; le JSON
  est conservé pour diagnostiquer ou restaurer. `AUTO_MIGRATE_DB=false` désactive
  ce mécanisme pour une intervention contrôlée.

## Paramètres de production

Le service est actuellement déployé depuis `web-app`; la fusion déclenchera le
déploiement automatique. La nouvelle version réutilise `DATABASE_URL` et
`SECRET_KEY`, déjà nécessaires à la version actuelle. `COOKIE_SECURE` garde sa
valeur par défaut sécurisée sur Render. L'accès administrateur utilise
`ADMIN_EMAIL` et `ADMIN_PASSWORD`; sans ces valeurs, le site public fonctionne,
mais la connexion admin n'est pas disponible.

## Variables requises pour la nouvelle version

Vérifier ces variables dans le service web Render avant la fusion. Ne jamais
copier leurs valeurs dans le dépôt, les logs ou un ticket :

| Variable | Valeur attendue |
| --- | --- |
| `DATABASE_URL` | URL **interne** de `Calculateur-Postgres`, récupérée depuis le tableau de bord Render. Ne pas la copier dans GitHub, les logs ou un ticket. |
| `SECRET_KEY` | Secret aléatoire fort, unique à l'application, conservé uniquement dans Render. |
| `ADMIN_EMAIL` | Adresse utilisée pour ouvrir l'espace administrateur. |
| `ADMIN_PASSWORD` | Mot de passe long et unique, conservé uniquement dans Render. |
| `COOKIE_SECURE` | `true` en production HTTPS. |

Render fournit lui-même la variable `RENDER`. Le code adapte les URL PostgreSQL `postgres://` et `postgresql://` au pilote `psycopg`.

### Pourquoi utiliser l'URL interne ?

Le service web et la base sont dans la même région Frankfurt. L'URL interne utilise le réseau privé Render et n'expose pas le trafic à Internet public. L'URL externe doit être réservée aux connexions venant de l'extérieur et nécessite TLS.

## Mise en service

1. Créer un snapshot ou un export PostgreSQL avant la première mise en service. Ne pas supposer que `notes.json` est complet ou durable. Les copies `localStorage` restent propres à chaque navigateur.
2. Vérifier `DATABASE_URL`, `SECRET_KEY` et, si l'espace admin est utilisé, `ADMIN_EMAIL` et `ADMIN_PASSWORD`. Privilégier l'URL interne PostgreSQL.
3. Confirmer que la CI passe, puis fusionner la PR. Le push sur `web-app` lance le déploiement Render.
4. Au démarrage, l'application valide tous les JSON avant migration. La migration s'exécute en transaction PostgreSQL et garde le JSON. Après migration, l'audit vérifie matières, notes et moyennes. Gunicorn ne sert les requêtes qu'après réussite de ces étapes.
5. Après le déploiement, vérifier les logs et les tables `anonymous_visitors`, `subjects` et `grades`, puis tester page publique, modification de notes, connexion admin, export JSON et cookies HTTPS.
6. Si le précontrôle échoue, le nouveau processus s'arrête sans modifier le schéma; consulter les profils signalés avant de relancer le déploiement. Prévoir un export avant l'expiration gratuite indiquée au **16 novembre 2026**.

## Limites connues à résoudre avant une utilisation sérieuse

- Le démarrage automatique exécute les migrations seulement lorsque `RENDER=true`; en local, utiliser `flask --app app db upgrade head`.
- La migration et le verrou PostgreSQL n'ont pas encore été exécutés sur une copie PostgreSQL dans cet environnement. Les tests de migration disponibles s'exécutent sur SQLite; il faut surveiller le premier démarrage Render et garder le snapshot prêt à restaurer.
- Flask-Limiter utilise actuellement le stockage mémoire : les compteurs sont réinitialisés au redémarrage et ne sont pas partagés entre plusieurs workers/instances.
- Les tests CI forcent `DATABASE_URL=sqlite:///:memory:` pour empêcher qu'ils touchent la base de production.

## Liens Render

- [Service web](https://dashboard.render.com/web/srv-das15460tbcc73ddu0eg)
- [Base PostgreSQL](https://dashboard.render.com/d/dpg-db9hqi5g1s2s738p1feg-a)

Cette procédure ne modifie pas directement les ressources Render; le démarrage de la nouvelle application appliquera la migration après la fusion.

## Synchronisation des données du navigateur

Le champ `anonymous_visitors.data_initialized` distingue un profil qui n'a jamais terminé sa première synchronisation d'un profil déjà initialisé.

1. Lors de la première visite avec un profil non initialisé, le navigateur envoie l'état trouvé dans `localStorage` à `/api/synchroniser`. Si aucune copie locale n'existe, il envoie l'état serveur courant, même vide, afin de terminer l'initialisation.
2. L'API valide les données avant de les enregistrer. Le contenu et le marqueur d'initialisation sont sauvegardés dans la même transaction.
3. Après cette première synchronisation réussie, l'état du serveur devient la référence. Si une copie locale diffère ensuite, le navigateur la remplace par l'état du serveur au lieu de pousser automatiquement une ancienne copie vers PostgreSQL.
4. Après les formulaires de modification, le navigateur récupère l'état serveur et actualise sa copie locale. En cas d'échec réseau ou d'écriture locale, le script ne supprime pas volontairement la copie locale.
5. Chaque page porte la version du carnet; les écritures comparent cette version à celle en base. Une version périmée reçoit HTTP 409, l'état serveur est rechargé et la modification doit être rejouée.

Cette politique permet de récupérer les données historiques d'un navigateur lors de son premier rattachement à un profil serveur. Elle ne peut pas fusionner automatiquement les données de plusieurs navigateurs : chacun a son propre cookie de profil et son propre `localStorage`.

### Schéma et migration

La révision `0001_relational_gradebook` ajoute `data_initialized` si nécessaire,
crée les tables relationnelles et copie les profils JSON existants. La révision
`0002_gradebook_version` ajoute le compteur de concurrence avec une valeur
initiale de 1 pour les profils existants. La base
Render inspectée le 17 octobre 2026 ne contenait aucune table; cette observation
est historique et doit être revérifiée avant toute migration. Les mises à jour
ultérieures du schéma doivent passer par de nouvelles révisions Alembic.

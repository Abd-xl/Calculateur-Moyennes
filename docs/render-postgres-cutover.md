# PostgreSQL sur Render : état et exploitation

> **État au 18 octobre 2026 : migration déployée et exécutée en production.**
> Ce document décrit l'état actuel et les contrôles qui restent à faire pour
> sécuriser l'exploitation de PostgreSQL.

## État vérifié au 18 octobre 2026

- Service web : `Calculateur-Moyennes`, région Frankfurt, branche de déploiement `web-app`, déploiement automatique activé.
- PostgreSQL : `Calculateur-Postgres`, PostgreSQL 18, même workspace et même région que le service.
- Base : `calculateur_postgres`.
- Les migrations `0001_relational_gradebook` et `0002_gradebook_version` ont été appliquées au démarrage du service; les tables `subjects` et `grades` sont présentes.
- Le dernier audit de production a compté **16 profils, 10 matières et 28 notes** dans le JSON et les tables relationnelles, sans écart entre les formats. Deux profils supplémentaires ont été créés depuis le contrôle initial; aucun contenu individuel n'a été exporté dans ce document.
- Le déploiement a exercé les migrations sur PostgreSQL de production. Les tests automatisés de migration en CI utilisent SQLite; ajouter une validation PostgreSQL reproductible reste utile.
- Cette instance reste la base primaire; aucune copie PostgreSQL indépendante n'est disponible dans le workspace Render.
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

Le service est déployé depuis `web-app`; les commits fusionnés déclenchent le
déploiement automatique. L'application utilise `DATABASE_URL` et `SECRET_KEY`.
`COOKIE_SECURE` garde sa
valeur par défaut sécurisée sur Render. L'accès administrateur utilise
`ADMIN_EMAIL` et `ADMIN_PASSWORD`; sans ces valeurs, le site public fonctionne,
mais la connexion admin n'est pas disponible.

## Variables de production

Vérifier ces variables dans le service web Render. Ne jamais
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

## Contrôles d'exploitation

1. Programmer un export/snapshot indépendant de PostgreSQL et documenter sa restauration; les copies `localStorage` ne remplacent pas une sauvegarde de base.
2. Privilégier `DATABASE_URL` interne depuis le service web et restreindre l'accès réseau PostgreSQL actuellement ouvert à `0.0.0.0/0`.
3. Vérifier après chaque déploiement les logs, la page publique, une modification de note, la connexion admin, l'export JSON et les cookies HTTPS.
4. Prévoir avant le **16 novembre 2026** une solution durable pour la base, dont l'offre gratuite arrive à expiration.

## Limites connues à résoudre avant une utilisation sérieuse

- Le démarrage automatique exécute les migrations seulement lorsque `RENDER=true`; en local, utiliser `flask --app app db upgrade head`.
- CI n'exerce pas encore la migration sur un PostgreSQL jetable; ajouter ce contrôle pour couvrir les particularités du moteur et éviter de dépendre de la production comme validation.
- Flask-Limiter utilise actuellement le stockage mémoire : les compteurs sont réinitialisés au redémarrage et ne sont pas partagés entre plusieurs workers/instances.
- Les tests CI forcent `DATABASE_URL=sqlite:///:memory:` pour empêcher qu'ils touchent la base de production.

## Liens Render

- [Service web](https://dashboard.render.com/web/srv-das15460tbcc73ddu0eg)
- [Base PostgreSQL](https://dashboard.render.com/d/dpg-db9hqi5g1s2s738p1feg-a)

Les migrations futures doivent passer par de nouvelles révisions Alembic. Le
démarrage vérifie l'état des gradebooks avant de servir les requêtes.

## Synchronisation des données du navigateur

Le champ `anonymous_visitors.data_initialized` distingue un profil qui n'a jamais terminé sa première synchronisation d'un profil déjà initialisé.

1. Lors de la première visite avec un profil non initialisé, le navigateur envoie l'état trouvé dans `localStorage` à `/api/synchroniser`. Si aucune copie locale n'existe, il envoie l'état serveur courant, même vide, afin de terminer l'initialisation.
2. L'API valide les données avant de les enregistrer. Le contenu et le marqueur d'initialisation sont sauvegardés dans la même transaction.
3. Après cette première synchronisation réussie, l'état du serveur devient la référence. Si une copie locale diffère ensuite, le navigateur la remplace par l'état du serveur au lieu de pousser automatiquement une ancienne copie vers PostgreSQL.
4. Si l'import initial échoue, la page affiche l'erreur, conserve la copie locale et propose de réessayer. Une sauvegarde téléchargeable contient la copie actuelle, la copie locale précédente et l'état serveur; l'application peut restaurer un fichier JSON ou la copie précédente après confirmation.
5. Après les formulaires de modification, le navigateur récupère l'état serveur et actualise sa copie locale. En cas d'échec réseau ou d'écriture locale, le script ne supprime pas volontairement la copie locale.
6. Chaque page porte la version du carnet; les écritures comparent cette version à celle en base. Une version périmée reçoit HTTP 409. L'import n'écrase pas automatiquement les données serveur en conflit; l'utilisateur doit confirmer la reprise.

Cette politique permet de récupérer les données historiques d'un navigateur lors de son premier rattachement à un profil serveur. Elle ne peut pas fusionner automatiquement les données de plusieurs navigateurs : chacun a son propre cookie de profil et son propre `localStorage`.

### Schéma et migration

La révision `0001_relational_gradebook` ajoute `data_initialized` si nécessaire,
crée les tables relationnelles et copie les profils JSON existants. La révision
`0002_gradebook_version` ajoute le compteur de concurrence avec une valeur
initiale de 1 pour les profils existants. La migration initiale a été appliquée
sur Render; les mises à jour ultérieures du schéma doivent passer par de
nouvelles révisions Alembic.

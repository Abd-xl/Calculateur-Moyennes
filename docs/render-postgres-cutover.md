# Préparation de la connexion PostgreSQL sur Render

> **État : procédure uniquement.** Cette documentation ne configure pas Render, ne lance pas de migration et ne déclenche aucun déploiement.

## État vérifié au 17 octobre 2026

- Service web : `Calculateur-Moyennes`, région Frankfurt, branche de déploiement `web-app`, déploiement automatique activé.
- PostgreSQL : `Calculateur-Postgres`, PostgreSQL 18, même workspace et même région que le service.
- Base : `calculateur_postgres`.
- La requête de lecture seule a confirmé que le schéma `public` contient actuellement **0 table**.
- Expiration indiquée pour l'offre gratuite : **16 novembre 2026**.
- L'accès réseau PostgreSQL comprend actuellement `0.0.0.0/0`. À revoir avant d'y stocker des données réelles.
- La branche `feature/admin-dashboard` utilise désormais Alembic. La révision
  `0001_relational_gradebook` crée les tables relationnelles et copie les
  données `anonymous_visitors.data` existantes. Elle garde le JSON synchronisé
  pendant la période de compatibilité. Ne pas exécuter `db.create_all()` ni
  lancer cette migration sur la production sans fenêtre de mise en service
  autorisée et sauvegarde vérifiée.

## Important : ne pas configurer la production trop tôt

Le service actuellement déployé utilise encore la branche `web-app` et l'ancienne architecture. **Ne pas lui ajouter maintenant les variables destinées à la nouvelle architecture.** La PR vers `web-app` déclenchera un déploiement automatique lorsqu'elle sera fusionnée. Les variables nécessaires devront être prêtes avant cette fusion, mais leur configuration nécessite une autorisation explicite.

## Variables requises pour la nouvelle version

Configurer ces variables dans le service web Render, uniquement lors de la fenêtre de mise en service autorisée :

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

## Ordre de mise en service (à exécuter seulement après autorisation)

1. **Sauvegarder et vérifier les données existantes.** Ne pas supposer que le fichier `notes.json` de l'ancienne version est complet ou durable sur Render. Les données de `localStorage` restent propres à chaque navigateur.
2. Dans le tableau de bord PostgreSQL, confirmer que la base est la bonne et récupérer l'URL interne depuis la section de connexion. Ne jamais enregistrer cette URL dans le dépôt.
3. Configurer les variables listées ci-dessus dans le service web. Vérifier visuellement les noms et ne pas partager les valeurs secrètes.
4. Confirmer la stratégie d'accès réseau PostgreSQL. L'URL interne est préférable ; réexaminer la règle `0.0.0.0/0` pour les connexions externes.
5. Vérifier une dernière fois que GitHub Actions passe sur le SHA de la PR et que les variables obligatoires sont présentes.
6. Avant toute migration réelle, restaurer une sauvegarde dans une copie jetable et y exécuter `flask --app app audit-gradebooks`. Résoudre les écarts et consigner les comptes JSON/relationnels.
7. Seulement après autorisation explicite, exécuter `flask --app app db upgrade head` contre la base visée pendant la fenêtre de mise en service et contrôler les comptes matières/notes.
8. Seulement après autorisation explicite, fusionner la PR. La branche `web-app` déploie automatiquement les commits.
9. Après le démarrage, vérifier les logs de déploiement, la présence des tables `anonymous_visitors`, `subjects` et `grades`, la page publique, les opérations de notes, la connexion administrateur, l'export JSON et les cookies HTTPS.
10. Prévoir un export/sauvegarde avant l'expiration gratuite indiquée au **16 novembre 2026**. Ne pas considérer la sauvegarde de la base comme un moyen de récupérer automatiquement les données `localStorage` de chaque navigateur.

## Limites connues à résoudre avant une utilisation sérieuse

- Le schéma n'est plus créé automatiquement au démarrage; la migration doit être appliquée avant de démarrer cette version.
- Flask-Limiter utilise actuellement le stockage mémoire : les compteurs sont réinitialisés au redémarrage et ne sont pas partagés entre plusieurs workers/instances.
- Les tests CI forcent `DATABASE_URL=sqlite:///:memory:` pour empêcher qu'ils touchent la base de production.

## Liens Render

- [Service web](https://dashboard.render.com/web/srv-das15460tbcc73ddu0eg)
- [Base PostgreSQL](https://dashboard.render.com/d/dpg-db9hqi5g1s2s738p1feg-a)

**Aucune modification Render, migration, fusion ou déploiement n'est effectué par cette procédure.**

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

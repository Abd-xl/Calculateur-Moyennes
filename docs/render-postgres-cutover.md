# Préparation de la connexion PostgreSQL sur Render

> **État : procédure uniquement.** Cette documentation ne configure pas Render, ne lance pas de migration et ne déclenche aucun déploiement.

## État vérifié au 17 octobre 2026

- Service web : `Calculateur-Moyennes`, région Frankfurt, branche de déploiement `web-app`, déploiement automatique activé.
- PostgreSQL : `Calculateur-Postgres`, PostgreSQL 18, même workspace et même région que le service.
- Base : `calculateur_postgres`.
- La requête de lecture seule a confirmé que le schéma `public` contient actuellement **0 table**.
- Expiration indiquée pour l'offre gratuite : **16 novembre 2026**.
- L'accès réseau PostgreSQL comprend actuellement `0.0.0.0/0`. À revoir avant d'y stocker des données réelles.
- L'application de la branche `feature/admin-dashboard` appelle `db.create_all()` au démarrage : lors de son premier démarrage avec une base vide, SQLAlchemy doit créer la table `anonymous_visitors`. Aucun `drop_all()` ni réinitialisation ne doit être exécuté contre la base de production.

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
6. Seulement après autorisation explicite, fusionner la PR. La branche `web-app` déploie automatiquement les commits.
7. Après le démarrage, vérifier les logs de déploiement, la présence de `anonymous_visitors`, la page publique, les opérations de notes, la connexion administrateur, l'export JSON et les cookies HTTPS.
8. Prévoir un export/sauvegarde avant l'expiration gratuite indiquée au **16 novembre 2026**. Ne pas considérer la sauvegarde de la base comme un moyen de récupérer automatiquement les données `localStorage` de chaque navigateur.

## Limites connues à résoudre avant une utilisation sérieuse

- `db.create_all()` crée les tables manquantes, mais ne remplace pas un système de migrations pour les futures modifications de schéma.
- Flask-Limiter utilise actuellement le stockage mémoire : les compteurs sont réinitialisés au redémarrage et ne sont pas partagés entre plusieurs workers/instances.
- Les tests CI forcent `DATABASE_URL=sqlite:///:memory:` pour empêcher qu'ils touchent la base de production.

## Liens Render

- [Service web](https://dashboard.render.com/web/srv-das15460tbcc73ddu0eg)
- [Base PostgreSQL](https://dashboard.render.com/d/dpg-db9hqi5g1s2s738p1feg-a)

**Aucune modification Render, migration, fusion ou déploiement n'est effectué par cette procédure.**

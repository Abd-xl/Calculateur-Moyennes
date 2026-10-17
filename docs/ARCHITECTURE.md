# Architecture — branche feature/admin-dashboard

## Interface publique sans connexion

- Le visiteur n'a pas besoin de créer un compte ni de se connecter.
- Au premier accès, Flask crée automatiquement un profil anonyme.
- Un jeton aléatoire est envoyé dans un cookie HTTP-only; la base conserve son hash plutôt que le jeton brut.
- Le profil contient un identifiant anonyme, les informations User-Agent envoyées par le navigateur, les dates de première visite et de dernière activité, ainsi que les notes et coefficients.
- Les routes publiques ne lisent et n'écrivent que les données associées au cookie courant.
- `localStorage` reste un mécanisme de récupération côté navigateur; il n'est pas une base de données cloud.

## Administration

- L'espace admin se trouve sous `/admin` et a une connexion séparée.
- Les identifiants viennent des variables d'environnement `ADMIN_EMAIL` et `ADMIN_PASSWORD`.
- Le tableau de bord permet de consulter les profils anonymes et d'exporter leurs données en JSON.
- Les routes admin ne sont pas accessibles sans session admin.
- Aucune adresse IP n'est stockée.

## Persistance

- PostgreSQL doit être configuré via `DATABASE_URL` sur Render.
- SQLite est utilisé par défaut pour le développement local.
- La base est initialisée avec `db.create_all()`; pour une application déjà en production, une migration SQL contrôlée sera nécessaire pour faire évoluer le schéma.

## Limites d'identification

L'identité représente un navigateur/profil de navigateur, pas une personne garantie. Supprimer le cookie, utiliser un autre navigateur ou naviguer en privé peut produire un nouveau profil. Le User-Agent ne permet pas d'identifier fiablement le nom réel de l'appareil.

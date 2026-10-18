# Calculateur-Moyennes — feuille de route

## État actuel

La branche `web-app` contient l'application Flask, une interface Jinja2, un
profil par navigateur, une persistance PostgreSQL/SQLAlchemy et l'ancienne
interface CLI. Le refactor principal et la migration du gradebook sont déployés;
les étapes ci-dessous suivent les travaux encore ouverts.

## Refactor

- [x] Extraire la fabrique d'application et préserver `gunicorn app:app`.
- [x] Séparer modèles, extensions, hooks de requête, routes admin et routes
  publiques.
- [x] Partager le calcul des moyennes entre l'application web et le CLI.
- [x] Extraire calculs et mutations des notes dans des services métier sans état global.
- [x] Déplacer la validation des données dans un service métier partagé.
- [x] Formaliser les adaptateurs JSON du CLI et SQLAlchemy du web derrière une
  API de persistance séparée.
- [x] Ajouter Alembic, le modèle relationnel et une migration JSON vers matières/notes.
- [x] Exécuter la migration PostgreSQL au démarrage et vérifier les comptes/totaux en production.
- [x] Ajouter un précontrôle en lecture seule des profils JSON avant migration.
- [x] Ajouter un audit en lecture seule du JSON et des gradebooks relationnels.
- [ ] Retirer la copie JSON après la période de compatibilité.
- [x] Migrer les profils JSON vers les tables relationnelles en conservant le JSON de repli.
- [x] Rendre visible l'échec de l'import navigateur et permettre la reprise depuis une sauvegarde.
- [x] Versionner l'état pour repérer les conflits de synchronisation.
- [x] Paginer l'admin, filtrer côté base et calculer les totaux côté base.
- [x] Permettre à l'administrateur de supprimer un profil et ses données depuis son détail.
- [x] Définir la conservation manuelle des profils jusqu'à leur suppression par l'administrateur.
- [x] Documenter l'export et les limites de suppression (notamment les copies locales navigateur).

## Contraintes

- Garder les URL existantes tant que les templates et les clients ne sont pas
  migrés.
- Ne pas modifier les variables Render ni déployer depuis cette branche sans
  une étape explicite de mise en service.
- Ne pas lancer de migration destructive; préparer et vérifier un chemin de
  retour avant de changer le schéma de production.

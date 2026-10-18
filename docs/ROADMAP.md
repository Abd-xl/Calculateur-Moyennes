# Calculateur-Moyennes — feuille de route

## État actuel

La branche `feature/admin-dashboard` contient l'application web Flask, une
interface Jinja2, un profil anonyme par navigateur, une persistance SQLAlchemy
et l'ancienne interface CLI. Le refactor est en cours; les étapes ci-dessous
distinguent le découpage déjà fait des changements qui touchent au stockage.

## Refactor

- [x] Extraire la fabrique d'application et préserver `gunicorn app:app`.
- [x] Séparer modèles, extensions, hooks de requête, routes admin et routes
  publiques.
- [x] Partager le calcul des moyennes entre l'application web et le CLI.
- [x] Extraire calculs et mutations des notes dans des services métier sans état global.
- [x] Déplacer la validation des données dans un service métier partagé.
- [ ] Formaliser les adaptateurs de persistance JSON du CLI et SQLAlchemy du web.
- [ ] Ajouter des migrations de schéma et normaliser matières et notes.
- [ ] Migrer les profils JSON avec sauvegarde, reprise et contrôle des totaux.
- [ ] Versionner l'état pour repérer les conflits de synchronisation.
- [ ] Paginer l'admin et calculer les totaux côté base.
- [ ] Définir conservation, export et suppression des données visiteurs.

## Contraintes

- Garder les URL existantes tant que les templates et les clients ne sont pas
  migrés.
- Ne pas modifier les variables Render ni déployer depuis cette branche sans
  une étape explicite de mise en service.
- Ne pas lancer de migration destructive; préparer et vérifier un chemin de
  retour avant de changer le schéma de production.

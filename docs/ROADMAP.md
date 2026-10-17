# Calculateur-Moyennes — feuille de route

## Produit

L'application principale est la version web hébergée sur Render. L'interface terminal reste disponible pour compatibilité, mais son stockage local `notes.json` est indépendant des profils web.

## Réalisé

- [x] Conserver l'ancienne CLI.
- [x] Ajouter des pages web Flask/Jinja2 et une interface responsive.
- [x] Conserver les notes avec leur barème original et calculer les moyennes sur /20.
- [x] Créer un profil anonyme par navigateur.
- [x] Persister les profils web via SQLAlchemy et `DATABASE_URL`.
- [x] Ajouter CSRF, cookies HTTP-only, authentification admin et limitation des tentatives.
- [x] Ajouter l'interface admin, la recherche, le détail des profils et l'export JSON.
- [x] Réduire le couplage entre stockage CLI et web.
- [x] Centraliser les validations, mutations de notes et calculs dans un module métier partagé.
- [x] Exclure de la moyenne générale les matières sans note.
- [x] Séparer les styles publics et admin.
- [x] Tester les routes, validations, calculs et index de notes avec SQLite en mémoire.

## Priorités suivantes

1. Revoir la confiance accordée à `X-Forwarded-For` pour le rate limiter sur Render et vérifier le comportement réel du proxy avant de considérer cette protection robuste.
2. Remplacer `db.create_all()` par des migrations explicites avant toute évolution du schéma.
3. Renvoyer des erreurs applicatives cohérentes et journalisées en cas d'échec de la base.
4. Envisager une pagination du tableau de bord admin si le nombre de profils augmente.
5. Finaliser le mode tableur ou masquer temporairement l'entrée tant que le mode n'est pas développé.
6. Améliorer progressivement les contrôles d'accessibilité et les tests navigateur du stockage local/synchronisation.
7. Étudier une PWA uniquement après stabilisation des interactions et de la sauvegarde des données.

## Principes

- Une responsabilité par module, sans fragmenter des fonctions qui sont naturellement liées.
- Les règles métier pures ne dépendent ni de Flask ni du stockage.
- Ne pas modifier le schéma ni les données de production sans procédure testée.
- Ne jamais committer de secrets.
- Tout changement de comportement de calcul ou d'action doit avoir un test de régression.
- La branche `administration` doit passer la CI et une revue avant fusion dans `web-app`.

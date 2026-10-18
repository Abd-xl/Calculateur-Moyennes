# Architecture — branche `feature/admin-dashboard`

## Architecture actuelle

```text
Navigateur
   ├── pages HTML rendues par Flask
   └── localStorage (copie de secours et import initial)
          │
          ▼
Routes publiques ───── Routes admin
          │                  │
          ├── services métier│
          ├── hooks visiteur │
          └── modèles SQLAlchemy
                    │
                    ▼
       anonymous_visitors.data (JSON)
```

Le point d'entrée historique `app.py` expose toujours `app:app` pour Gunicorn.
La fabrique `calculateur.create_app()` configure l'application, les extensions,
les routes et les hooks de requête. `calculateur/services/grades.py` contient les
calculs partagés et `calculateur/services/gradebook.py` les mutations métier
sans état global. Le CLI conserve `gestion_note.py` comme adaptateur vers le JSON
local. Les routes publiques et admin sont enregistrées séparément tout en
conservant les URL et les noms d'endpoint existants.

Le format JSON stocké par visiteur reste `{"notes": {...}, "coef": {...}}`.
`localStorage` sert à récupérer les anciennes données lors de la première
synchronisation et conserve ensuite une copie locale; PostgreSQL reste la source
de vérité après l'initialisation.

## Persistance et déploiement

- PostgreSQL est configuré avec `DATABASE_URL`; SQLite sert au développement.
- `db.create_all()` est conservé temporairement pour maintenir le démarrage
  existant. Il ne remplace pas des migrations pour les évolutions de schéma.
- Flask-Limiter utilise `RATELIMIT_STORAGE_URI`, avec `memory://` par défaut.
- Les routes admin sont protégées par la session Flask et les identifiants
  `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
- `SECRET_KEY` est obligatoire lorsque `RENDER=true`.

La procédure de préparation PostgreSQL, les étapes de mise en service et les
limites connues sont documentées dans
[`render-postgres-cutover.md`](render-postgres-cutover.md). Aucun changement de
base ou de déploiement ne fait partie du refactor local.

## Étapes de refactor

1. Extraire la fabrique Flask, les extensions, les modèles, les hooks, les
   groupes de routes et les règles métier tout en gardant les URL, le schéma et
   le point d'entrée.
2. Formaliser la frontière de persistance entre le CLI JSON et le web
   SQLAlchemy.
3. Introduire des migrations de base et un modèle relationnel de matières et de
   notes, avec une migration réversible depuis le JSON existant.
4. Définir une stratégie de synchronisation versionnée pour détecter les
   modifications simultanées venant de plusieurs onglets ou appareils.

Les étapes 3 et 4 nécessitent une sauvegarde et une procédure de migration avant
toute mise en production.

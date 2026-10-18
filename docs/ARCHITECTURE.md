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
   ├── services métier│      ├── agrégats SQL paginés
   ├── hooks visiteur │      └── adaptateur gradebook
   └── adaptateur SQLAlchemy
                    │
                    ▼
      visiteurs, matières et notes
          └── JSON de compatibilité
```

Le point d'entrée historique `app.py` expose toujours `app:app` pour Gunicorn.
La fabrique `calculateur.create_app()` configure l'application, les extensions,
les routes et les hooks de requête. `calculateur/services/grades.py` contient les
calculs partagés et `calculateur/services/gradebook.py` les mutations métier
sans état global. Le CLI conserve `gestion_note.py` comme adaptateur vers le JSON
local. Les routes publiques et admin sont enregistrées séparément tout en
conservant les URL et les noms d'endpoint existants.

`calculateur/repositories/visitor_gradebook.py` isole les lectures et écritures
des données web. `calculateur/repositories/json_file.py` is l'adaptateur du CLI;
`sauvegarde.py` conserve temporairement l'API historique autour de cet adaptateur.
Les deux adaptateurs valident le même format métier.

L'administration filtre et pagine les visiteurs en base. Ses compteurs globaux
et les nombres de matières/notes par profil sont agrégés depuis les tables
relationnelles; les détails et l'export passent par l'adaptateur gradebook.

Le format JSON stocké par visiteur reste `{"notes": {...}, "coef": {...}}`.
`localStorage` sert à récupérer les anciennes données lors de la première
synchronisation et conserve ensuite une copie locale; PostgreSQL reste la source
de vérité après l'initialisation.

## Persistance et déploiement

- PostgreSQL est configuré avec `DATABASE_URL`; SQLite sert au développement.
- Les migrations Flask-Migrate/Alembic définissent le schéma. La révision
  `0001_relational_gradebook` conserve le JSON et copie les profils vers les
  tables relationnelles; `0002_gradebook_version` ajoute une version de carnet.
- Le champ JSON reste synchronisé pendant la période de compatibilité et sert
  de format de repli lors d'un downgrade.
- Les écritures du navigateur joignent leur version courante. Une mise à jour
  conditionnelle refuse une version périmée avec HTTP 409 et renvoie l'état
  serveur à recharger au lieu d'écraser les changements concurrents.
- `flask --app app audit-gradebooks` compare en lecture seule le JSON de
  compatibilité, les matières/notes relationnelles et les moyennes par lots.
- `flask --app app preflight-gradebooks` valide en lecture seule le JSON source
  et établit les comptes de référence avant la migration.
- Flask-Limiter utilise `RATELIMIT_STORAGE_URI`, avec `memory://` par défaut.
- Les routes admin sont protégées par la session Flask et les identifiants
  `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
- Depuis le détail d'un profil, l'administrateur peut le supprimer par POST
  protégé par CSRF; les matières et notes liées sont supprimées avec lui.
- `GET /admin/export.json` exporte tous les profils, leurs identifiants anonymes,
  les informations navigateur, les dates et les carnets de notes; l'admin exige
  une session authentifiée. L'export lit les profils par lots de 100 et les
  réponses `/admin` portent `Cache-Control: no-store` pour éviter leur mise en
  cache.
- Supprimer un profil efface ses données côté serveur, mais ne supprime pas les
  fichiers d'export déjà téléchargés, les sauvegardes de base ni les copies
  `localStorage` conservées sur les appareils des visiteurs.
- Les profils sont conservés jusqu'à leur suppression manuelle par
  l'administrateur; aucune purge automatique n'est prévue.
- `SECRET_KEY` est obligatoire lorsque `RENDER=true`.

La procédure de préparation PostgreSQL, les étapes de mise en service et les
limites connues sont documentées dans
[`render-postgres-cutover.md`](render-postgres-cutover.md). Aucun changement de
base ou de déploiement ne fait partie du refactor local.

## Étapes de refactor

1. Extraire la fabrique Flask, les extensions, les modèles, les hooks, les
   groupes de routes et les règles métier tout en gardant les URL, le schéma et
   le point d'entrée.
2. Vérifier la migration dans un environnement de développement et établir un
   contrôle des comptes/totaux avant toute utilisation avec des données réelles.
3. La version du carnet détecte les modifications simultanées; définir ensuite
   une stratégie de fusion si l'on veut combiner les modifications concurrentes.

Avant toute mise en production, vérifier la migration sur une copie de données,
confirmer les comptes et totaux, et définir la procédure de synchronisation
multi-appareils.

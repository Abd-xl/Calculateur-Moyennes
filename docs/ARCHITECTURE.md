# Architecture du calculateur

## Vue d'ensemble

La version principale est l'application web Flask hébergée sur Render. L'ancienne interface terminal est conservée, mais ses données locales `notes.json` sont indépendantes des profils web stockés en base.

```text
Navigateur web
    │
    ▼
Routes Flask (calculateur/routes/)
    │
    ├── Règles métier pures ──> domaine.py
    │
    └── Service de profil ──> calculateur/services.py
                                  │
                                  ▼
                              SQLAlchemy
                                  │
                                  ▼
                         anonymous_visitors

CLI historique ──> gestion_note.py ──> domaine.py
        │
        └─────────────────────────> sauvegarde.py ──> notes.json
```

## Responsabilités

- `app.py` est le point d'entrée WSGI conservé pour `gunicorn app:app`.
- `calculateur/__init__.py` crée l'application Flask, lit la configuration et enregistre les extensions, hooks et routes.
- `calculateur/extensions.py` contient les extensions partagées.
- `calculateur/models.py` décrit le modèle SQLAlchemy `Visitor`.
- `calculateur/security.py` gère l'identification anonyme d'un navigateur et la protection des routes admin.
- `calculateur/routes/public.py` contient les pages du calculateur et l'API de synchronisation.
- `calculateur/routes/admin.py` contient la connexion admin, le tableau de bord, le détail des profils et l'export.
- `calculateur/services.py` lit et persiste l'état du profil web courant.
- `domaine.py` regroupe les calculs, validations et mutations de données sans dépendance Flask ni accès au stockage.
- `gestion_note.py`, `sauvegarde.py`, `cli.py` et `main.py` conservent l'ancienne interface terminale.

Les modules ne sont séparés que lorsque la responsabilité ou les effets de bord diffèrent. Les fonctions métier pures doivent rester partagées plutôt que recopiées dans les routes web et la CLI.

## Profils anonymes et administration

- Le serveur crée un profil lors de la première requête d'un navigateur.
- Un jeton aléatoire est placé dans un cookie HTTP-only; seule son empreinte SHA-256 est stockée en base.
- La base conserve un identifiant anonyme, le User-Agent déclaré par le client, les dates de visite et les notes.
- Le profil identifie un navigateur/profil et non une personne garantie.
- Les routes admin sont sous `/admin` et protégées par la session `admin_authenticated`.
- Les identifiants admin viennent des variables d'environnement `ADMIN_EMAIL` et `ADMIN_PASSWORD`.
- CSRF, cookies HTTP-only, politique SameSite et limite de tentatives de connexion sont conservés.

### Limites à examiner en revue sécurité

Le limiteur lit `X-Forwarded-For` sur Render. Le code suppose que le premier élément représente l'IP cliente; cette hypothèse doit rester vérifiée dans la configuration réelle du proxy, car une valeur d'en-tête non fiable peut permettre de contourner une limite de débit. Le limiteur utilise en outre un stockage mémoire par défaut; ses compteurs ne sont pas partagés entre plusieurs processus ou instances.

## Persistance et migrations

- Render : PostgreSQL via `DATABASE_URL`.
- Local : SQLite par défaut.
- L'ancienne CLI continue d'utiliser `notes.json`.
- Le modèle `anonymous_visitors` conserve ses colonnes actuelles.
- `db.create_all()` crée les tables manquantes; ce n'est pas un système de migration. Toute évolution ultérieure du schéma doit passer par une migration explicite, vérifiée et documentée.

## Règle de calcul

Les notes sont enregistrées avec leur barème d'origine puis converties sur /20 pour le calcul. La moyenne d'une matière sans note est affichée à 0 pour la présentation, mais une matière sans évaluation est exclue du dénominateur de la moyenne générale : l'absence de note ne vaut pas une note de zéro.

## Tests

Les tests automatisés utilisent SQLite en mémoire via `tests/conftest.py`. Ils ne doivent jamais ouvrir de connexion à la base de données de production.

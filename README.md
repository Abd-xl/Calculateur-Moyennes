# Calculateur de moyennes

Application web de gestion de notes scolaires, développée avec Flask et hébergée sur Render. Elle permet de saisir des notes sur /10 ou /20, de calculer les moyennes par matière et la moyenne générale pondérée, et de retrouver ses données depuis un navigateur.

**Application en ligne :** https://calculateur-moyennes.onrender.com

> La version web de production est déployée depuis la branche `web-app`. Les changements sur la branche `administration` restent en revue et ne sont pas mis en production avant fusion.

## Fonctionnalités web

- Notes sur /10 ou /20, avec conservation du barème d'origine.
- Moyennes par matière et moyenne générale pondérée par les coefficients.
- Ajout, modification et suppression de notes et de matières.
- Profil anonyme par navigateur, sans compte utilisateur public.
- Synchronisation des données avec le serveur et sauvegarde de secours dans le navigateur.
- Interface sombre adaptée au mobile et au desktop.
- Tableau de bord administrateur protégé, consultation des profils et export JSON.

Le mode tableur est encore un emplacement de fonctionnalité à développer.

## Utiliser l'ancienne interface terminal

Le dépôt conserve l'ancienne interface Python en ligne de commande. Elle utilise le fichier local `notes.json`, indépendamment des profils web stockés en base de données.

```bash
python main.py
```

Cette commande est destinée à l'utilisation locale de l'ancienne version. Les données CLI dans `notes.json` ne sont pas les données des visiteurs de l'application web Render.

## Architecture technique

```text
app.py                  Point d'entrée WSGI : gunicorn app:app
domaine.py              Validation, règles métier et calculs partagés
calculateur/
├── __init__.py         Fabrique Flask et configuration
├── extensions.py       SQLAlchemy, CSRF et limiteur de débit
├── models.py           Modèle SQL Visitor
├── security.py         Identification anonyme et protection admin
├── services.py         Lecture et sauvegarde du profil courant en base
└── routes/
    ├── public.py       Pages web et API de synchronisation
    └── admin.py        Administration et export
gestion_note.py         Ancien service métier de la CLI
sauvegarde.py           Ancienne persistance JSON de la CLI
cli.py / main.py        Entrée terminale historique
templates/              Templates Jinja2
static/style.css        Styles de l'application publique
static/admin.css        Styles de l'administration
static/local_storage.js Sauvegarde et synchronisation côté navigateur
tests/                  Tests automatisés
docs/                   Architecture, feuille de route et journal
```

Le module `domaine.py` ne dépend ni de Flask ni du stockage : il regroupe les calculs et validations réutilisés par la CLI et le web. La persistance est séparée : `sauvegarde.py` écrit le fichier JSON historique, alors que `calculateur/services.py` utilise SQLAlchemy pour les profils web.

## Installation locale pour contribuer

Prérequis : Python 3.12 ou version compatible avec les dépendances listées.

```bash
git clone https://github.com/Abd-xl/Calculateur-Moyennes.git
cd Calculateur-Moyennes
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt pytest
python app.py
```

Sur Windows, l'activation de l'environnement virtuel se fait avec `.venv\\Scripts\\activate`.

Par défaut, l'application web locale utilise SQLite dans `calculateur.db`. Pour travailler sur les modifications destinées à Render, utilise une branche de développement et une base de test : ne connecte pas les tests à la base de production.

## Déploiement Render

La commande de démarrage actuelle est :

```bash
gunicorn app:app
```

Le service web de production utilise PostgreSQL via `DATABASE_URL`. Les variables de configuration attendues sont :

- `DATABASE_URL` : URL PostgreSQL de production.
- `SECRET_KEY` : clé secrète longue et aléatoire pour les sessions.
- `ADMIN_EMAIL` et `ADMIN_PASSWORD` : identifiants de l'espace administrateur.
- `COOKIE_SECURE=true` : attribut Secure pour les cookies sur HTTPS.
- `RATELIMIT_STORAGE_URI` : facultatif. Un stockage partagé est recommandé si plusieurs workers ou instances doivent partager la même limite de débit.

Configure ces valeurs dans le tableau de bord Render, jamais dans le code source. Le démarrage en production doit se faire avec Gunicorn, pas avec le serveur de développement Flask. Aucune migration de schéma n'est automatisée par ce dépôt à ce stade.

## Administration et confidentialité

La connexion administrateur est accessible à `/admin/connexion`. Le tableau de bord se trouve à `/admin`.

L'identifiant anonyme correspond à un navigateur/profil, pas à une personne garantie. Effacer le cookie ou utiliser un autre navigateur peut créer un nouveau profil. Le User-Agent est déclaré par le client et ne prouve pas le modèle physique de l'appareil.

## Tests

```bash
python -m pytest -q
```

Les tests utilisent SQLite en mémoire et ne doivent jamais viser la base PostgreSQL de production.

Pour la structure et les décisions techniques, consulter `docs/ARCHITECTURE.md`, `docs/ROADMAP.md` et `docs/JOURNAL.md`.

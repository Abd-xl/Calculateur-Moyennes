# Calculateur de moyennes

Application de gestion de notes scolaires, d'abord développée en Python en ligne de commande, puis transformée en application web avec Flask.

Le projet conserve son cœur métier Python et une interface HTML/CSS responsive.

## Version actuelle

**Application web locale-first — branche `feature/local-first-storage`**

### Fonctionnalités

- Ajout de notes par matière, sur **/10 ou /20**.
- Conservation du barème original de chaque note.
- Calcul des moyennes sur une base commune de /20.
- Coefficient par matière et moyenne générale pondérée.
- Modification et suppression des notes et des matières.
- Détection des matières malgré les espaces superflus ou les différences de casse.
- Stockage durable des données web dans le `localStorage` du navigateur.
- Sauvegarde JSON téléchargeable, import JSON et restauration d'une copie locale précédente.
- Ancienne interface terminal conservée avec sa sauvegarde `notes.json`.

> Le mode « Remplir le tableur » est encore en développement.
>
> L'espace administrateur reste présent comme page d'information, mais il est désactivé : il ne consulte plus de profils et ne propose ni connexion, ni suppression, ni export centralisé.

## Architecture

```text
Navigateur
   ├── interface servie par Flask
   ├── localStorage (source durable des données web)
   └── sauvegardes JSON (export/import contrôlé par l'utilisateur)
          │
          ▼
Routes Flask
   └── cache mémoire temporaire
       (rendu des pages et détection des conflits)
```

Le cache mémoire Flask n'est pas une base de données et ne constitue pas une sauvegarde. Il peut disparaître lors d'un redémarrage ou lorsqu'un profil est évincé du cache. Au prochain chargement, le navigateur réhydrate ce cache depuis son `localStorage`.

**Conséquences :**
- Les données web appartiennent à un navigateur et à son stockage local.
- Il n'y a plus de synchronisation entre appareils ou navigateurs.
- Effacer les données du site, changer de navigateur ou perdre l'appareil peut faire perdre les données non exportées.
- L'application web nécessite JavaScript et une connexion au serveur pour charger l'interface.
- Le déploiement Render doit utiliser **un seul worker Gunicorn** : plusieurs workers auraient des caches indépendants.
- Pour changer d'appareil, utiliser une sauvegarde JSON et l'importer sur l'autre navigateur.

## Structure principale

```text
.
├── app.py
├── calculateur/
│   ├── __init__.py
│   ├── extensions.py
│   ├── request_hooks.py
│   ├── repositories/
│   │   ├── json_file.py
│   │   └── memory_gradebook.py
│   ├── routes/
│   │   ├── public.py
│   │   └── admin.py
│   └── services/
│       ├── gradebook.py
│       ├── grades.py
│       └── validation.py
├── static/
│   ├── local_storage.js
│   └── style.css
├── templates/
├── tests/
├── gestion_note.py
├── sauvegarde.py
├── main.py
└── requirements.txt
```

Le service métier `calculateur/services/` reste indépendant de Flask et du stockage. `memory_gradebook.py` ne conserve qu'un cache temporaire pour rendre les pages et gérer les versions concurrentes. `local_storage.js` conserve les données du navigateur et gère les imports/exports JSON.

## Installation locale

```bash
git clone https://github.com/Abd-xl/Calculateur-Moyennes.git
cd Calculateur-Moyennes
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

L'application est accessible à l'adresse locale indiquée par Flask.

Pour Gunicorn :

```bash
gunicorn --workers 1 app:app
```

### Interface terminal

L'ancienne version en ligne de commande reste disponible :

```bash
python main.py
```

Elle conserve son propre fichier `notes.json`, indépendant du stockage de l'application web.

## Déploiement Render

- Build : `pip install -r requirements.txt`
- Start : `gunicorn --workers 1 app:app`
- Variable obligatoire : `SECRET_KEY`, une valeur aléatoire et privée.
- `COOKIE_SECURE=true` peut être conservé pour HTTPS.

Aucune variable `DATABASE_URL` n'est requise. PostgreSQL, SQLite applicatif, SQLAlchemy et Alembic ne sont plus utilisés par l'application web.

## Tests

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q
```

## Historique des versions

### 2.1.0 — stockage local-first
- Remplacement de la persistance PostgreSQL par `localStorage` comme stockage durable du navigateur.
- Ajout d'un cache mémoire temporaire pour préserver les pages Flask existantes.
- Conservation de l'import/export et de la restauration JSON.
- Désactivation de l'administration des profils.

### 2.0.0 — 2026-09-26
- Transition de l'application terminal vers une interface web Flask.
- Ajout de l'interface HTML/CSS/Jinja2.
- Ajout des routes de gestion des notes, des matières et des sauvegardes.
- Déploiement initial de la branche `web-app` sur Render.

## Auteur

**Abd-xl**

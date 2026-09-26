# Calculateur de moyennes

Application de gestion de notes scolaires, développée en Python et progressivement adaptée à une interface web avec Flask.

Le projet a commencé comme une application en ligne de commande utilisant un fichier JSON pour la persistance des données. La branche `web-app` constitue l'évolution vers une application web tout en conservant le cœur métier du projet.

## Fonctionnalités actuelles

- Ajout de notes par matière.
- Attribution d'un coefficient à chaque matière.
- Calcul de la moyenne de chaque matière.
- Calcul de la moyenne générale pondérée.
- Modification d'une note.
- Suppression d'une note.
- Suppression d'une matière.
- Sauvegarde automatique dans `notes.json`.
- Interface web avec Flask et Jinja2.
- Gestion des erreurs de validation côté logique métier.

## Structure

```text
.
├── app.py
├── gestion_note.py
├── main.py
├── sauvegarde.py
├── notes.json
├── templates/
│   └── index.html
└── docs/
    ├── ARCHITECTURE.md
    ├── JOURNAL.md
    └── ROADMAP.md
```

### Rôle des principaux fichiers

- `app.py` : routes Flask et gestion des requêtes HTTP.
- `gestion_note.py` : logique métier du calculateur.
- `sauvegarde.py` : chargement et sauvegarde des données.
- `main.py` : ancienne interface en ligne de commande.
- `templates/index.html` : interface HTML rendue par Flask.
- `notes.json` : données persistées localement.

## Installation

### Prérequis

- Python 3.x
- Flask

### Application web

Cloner le dépôt :

```bash
git clone https://github.com/Abd-xl/Calculateur-Moyennes.git
cd Calculateur-Moyennes
```

Installer Flask :

```bash
pip install flask
```

Lancer l'application :

```bash
python app.py
```

L'application est ensuite accessible sur le serveur local indiqué par Flask.

### Version terminal

L'ancienne interface CLI reste disponible avec :

```bash
python main.py
```

## Architecture

La branche `web-app` suit actuellement une séparation simple des responsabilités :

```text
Navigateur
    │
    ▼
Routes Flask (app.py)
    │
    ▼
Logique métier (gestion_note.py)
    │
    ▼
Persistance (sauvegarde.py)
    │
    ▼
notes.json
```

Les interfaces ne doivent pas dupliquer les règles de gestion des notes. Les opérations comme l'ajout, la modification et la suppression sont centralisées dans la logique métier.

## Développement

Le projet évolue progressivement afin de conserver une base compréhensible et testable à chaque étape.

Les décisions d'architecture et les étapes importantes sont documentées dans :

- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/JOURNAL.md`

La prochaine phase concerne l'amélioration de l'interface et son adaptation aux écrans mobiles.

## Historique

### 1.2.0 — 2026-06-11
- Réorganisation du projet en plusieurs modules.
- Renforcement de la validation des données.
- Amélioration de la gestion des sauvegardes.

### 1.1.0 — 2026-05-21
- Ajout de la modification d'une note.

### 1.0.0 — 2026-05-20
- Ajout du menu de modification et de suppression.
- Suppression d'une matière.
- Réinitialisation des données.
- Sauvegarde JSON.

### 0.1.0 — 2026-05-16
- Première version du calculateur de moyennes.

## Auteur

**Abd-xl**

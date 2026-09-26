# Calculateur de moyennes

Application de gestion de notes scolaires, d'abord développée en Python en ligne de commande, puis progressivement transformée en application web avec Flask.

Le projet conserve son cœur métier Python tout en ajoutant une interface HTML/CSS adaptée à une utilisation sur ordinateur et mobile.

## Version actuelle

**2.0.0 — branche `web-app`**

Cette version marque la transition du projet vers une application web Flask.

### Fonctionnalités actuelles

- Ajout de notes par matière.
- Notes sur **/10 ou /20**.
- Conservation du barème original de chaque note.
- Calcul des moyennes sur une base commune de /20.
- Coefficient pour chaque matière.
- Calcul de la moyenne générale pondérée.
- Modification d'une note.
- Suppression d'une note.
- Suppression d'une matière.
- Détection des matières existantes malgré les espaces superflus ou les différences de casse.
- Sauvegarde des données dans `notes.json`.
- Interface web avec Flask et Jinja2.
- Interface sombre et responsive avec HTML/CSS.
- Fenêtres `dialog` pour modifier les notes sans agrandir les lignes du tableau.
- Sélection rapide d'une matière existante lors de l'ajout d'une note.
- Ancienne interface terminal conservée.

> Le mode « Remplir le tableur » est encore en développement.

## Structure

```text
.
├── app.py
├── gestion_note.py
├── sauvegarde.py
├── main.py
├── notes.json
├── requirements.txt
├── templates/
│   ├── index.html
│   ├── ajouter.html
│   ├── notes.html
│   └── tableur.html
├── static/
│   └── style.css
└── docs/
    ├── ARCHITECTURE.md
    ├── JOURNAL.md
    └── ROADMAP.md
```

### Rôle des principaux fichiers

- `app.py` : routes Flask et gestion des requêtes HTTP.
- `gestion_note.py` : logique métier du calculateur et calcul des moyennes.
- `sauvegarde.py` : chargement et sauvegarde des données JSON.
- `main.py` : ancienne interface en ligne de commande.
- `templates/index.html` : tableau de bord principal.
- `templates/ajouter.html` : ajout d'une note à une matière existante ou création d'une matière.
- `templates/notes.html` : affichage de toutes les notes.
- `templates/tableur.html` : emplacement du futur mode tableur.
- `static/style.css` : styles de l'interface web.
- `notes.json` : données persistées localement.

## Modèle des notes

Une note conserve désormais sa valeur et son barème d'origine.

Par exemple :

```json
{
  "note": 10,
  "bareme": 10
}
```

représente bien **10/10**, et non une note déjà convertie en 20/20.

La conversion sur /20 est effectuée uniquement pendant le calcul :

```text
10/10 → 20/20
5/20  → 5/20
```

Cela permet d'afficher la note telle qu'elle a été saisie tout en utilisant une échelle commune pour les calculs.

## Architecture

La branche `web-app` suit actuellement cette architecture :

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

Les interfaces ne doivent pas dupliquer les règles de gestion. Les opérations comme l'ajout, la modification, la suppression et le calcul sont centralisées dans la logique métier.

## Installation

### Prérequis

- Python 3.x
- pip

### Installation

Cloner le dépôt :

```bash
git clone https://github.com/Abd-xl/Calculateur-Moyennes.git
cd Calculateur-Moyennes
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

### Application web

Lancer Flask :

```bash
python app.py
```

L'application est ensuite accessible à l'adresse locale indiquée par Flask.

Pour un serveur de production utilisant Gunicorn :

```bash
gunicorn app:app
```

### Version terminal

L'ancienne interface CLI reste disponible avec :

```bash
python main.py
```

## Déploiement

La branche `web-app` est déployée sur Render.

La configuration utilise :

```text
Build : pip install -r requirements.txt
Start : gunicorn app:app
```

La persistance actuelle repose encore sur `notes.json`. Une base de données, d'abord SQLite puis éventuellement PostgreSQL, est prévue pour une évolution plus robuste.

## Développement

Le projet évolue progressivement afin de conserver une base compréhensible et testable à chaque étape.

Les décisions techniques et les changements importants sont documentés dans :

- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/JOURNAL.md`

### Prochaines étapes

- Finaliser le mode tableur.
- Améliorer l'expérience mobile.
- Ajouter progressivement l'interactivité JavaScript.
- Étudier le fonctionnement hors ligne.
- Transformer progressivement l'application en PWA.
- Remplacer le stockage JSON par une vraie base de données lorsque nécessaire.
- Ajouter les mesures de sécurité adaptées au déploiement.

## Historique des versions

### 2.0.0 — 2026-09-26
- Transition de l'application terminal vers une interface web Flask.
- Ajout de l'interface HTML/CSS/Jinja2.
- Ajout des routes dédiées pour les opérations sur les notes et les matières.
- Ajout du tableau de bord avec moyenne générale et tableau des matières.
- Ajout des fenêtres `dialog` pour modifier et supprimer les notes.
- Ajout de la page dédiée à l'ajout d'une note.
- Ajout de la prise en charge des notes sur /10 et /20.
- Conservation du barème original dans les données.
- Ajout de la détection des matières malgré les espaces superflus et les différences de casse.
- Ajout de `requirements.txt` et préparation du déploiement avec Gunicorn.
- Déploiement de la branche `web-app` sur Render.

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

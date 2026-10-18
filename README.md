# Calculateur de moyennes

Application de gestion de notes scolaires, d'abord développée en Python en ligne de commande, puis progressivement transformée en application web avec Flask.

Le projet conserve son cœur métier Python tout en ajoutant une interface HTML/CSS adaptée à une utilisation sur ordinateur et mobile.

## Version actuelle

**2.0.0 — refactor en cours sur `feature/admin-dashboard`**

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
- Sauvegarde CLI historique dans `notes.json`.
- Profils web anonymes avec persistance SQLAlchemy.
- Interface web avec Flask et Jinja2.
- Interface sombre et responsive avec HTML/CSS.
- Fenêtres `dialog` pour modifier les notes sans agrandir les lignes du tableau.
- Sélection rapide d'une matière existante lors de l'ajout d'une note.
- Ancienne interface terminal conservée.

> Le mode « Remplir le tableur » est encore en développement.

## Structure

```text
.
├── app.py                         Point d'entrée compatible avec Gunicorn
├── calculateur/
│   ├── __init__.py                 Fabrique Flask
│   ├── extensions.py               Extensions Flask
│   ├── models.py                   Modèles SQLAlchemy
│   ├── request_hooks.py             Identification du profil navigateur
│   ├── security.py                  Authentification et IP cliente
│   ├── routes/
│   │   ├── public.py                Pages et API publiques
│   │   └── admin.py                 Espace administrateur
│   ├── repositories/                Adaptateurs JSON et SQLAlchemy
│   └── services/                     Calculs et mutations métier partagés
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

- `app.py` : point d'entrée Flask conservé pour `gunicorn app:app`.
- `calculateur/` : application web organisée par extensions, modèles, hooks,
  routes et services.
- `calculateur/services/` : règles de calcul et mutations indépendantes des
  requêtes HTTP et de la sauvegarde.
- `gestion_note.py` : opérations historiques utilisées par l'interface CLI;
  les calculs sont partagés avec le service web.
- `sauvegarde.py` : chargement et sauvegarde des données JSON.
- `main.py` : ancienne interface en ligne de commande.
- `templates/index.html` : tableau de bord principal.
- `templates/ajouter.html` : ajout d'une note à une matière existante ou création d'une matière.
- `templates/notes.html` : affichage de toutes les notes.
- `templates/tableur.html` : emplacement du futur mode tableur.
- `static/style.css` : styles de l'interface web.
- `notes.json` : persistance locale de l'ancienne interface CLI.

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

La branche `feature/admin-dashboard` suit actuellement cette architecture :

```text
Navigateur
    │
    ▼
Fabrique Flask (calculateur/)
    │
    ▼
Routes publiques et admin
    │
    ▼
Service de calcul + modèles SQLAlchemy
    │
    ▼
PostgreSQL / SQLite (état web) + localStorage (copie navigateur)
```

Le calcul des moyennes est partagé entre le web et le CLI. L'extraction des
validations et mutations en services métier indépendants est la prochaine étape.

## Installation

### Prérequis

- Python 3.x
- pip

### Installation

Cloner le dépôt :

```bash
git clone https://github.com/Abd-xl/Calculateur-Moyennes.git
cd Calculateur-Moyennes
git switch feature/admin-dashboard
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

### Application web

Initialiser ou mettre à niveau le schéma local avec la migration versionnée :

```bash
flask --app app db upgrade head
```

Sur une copie jetable de la base, comparer le JSON de compatibilité avec les
tables relationnelles et vérifier les comptes et moyennes :

```bash
flask --app app audit-gradebooks
```

Cette commande est en lecture seule; elle retourne un code d'erreur si elle
trouve un profil incohérent.

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

Le service Render continue de déployer `web-app`. Cette branche de refactor
utilise `DATABASE_URL` pour PostgreSQL en production et SQLite par défaut en
local. Le schéma doit être mis à niveau avec `flask --app app db upgrade` avant
de démarrer la nouvelle version. Aucun changement de déploiement n'est effectué
par ce refactor.

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




## Architecture anonyme (branche `feature/admin-dashboard`)

L'interface publique ne demande aucun compte ni mot de passe. Le serveur crée automatiquement un profil anonyme par navigateur à partir d'un jeton aléatoire conservé dans un cookie HTTP-only. La base stocke uniquement le hash du jeton, un identifiant anonyme, le User-Agent déclaré par le navigateur et les notes.

L'espace administrateur est séparé et protégé par `ADMIN_EMAIL` et `ADMIN_PASSWORD`. La base de données de production doit être PostgreSQL via `DATABASE_URL`; SQLite est prévu pour le développement local.

Variables de déploiement :
- `DATABASE_URL` : URL PostgreSQL persistante.
- `SECRET_KEY` : secret aléatoire long pour les sessions.
- `ADMIN_EMAIL` et `ADMIN_PASSWORD` : identifiants de l'espace administrateur.
- `COOKIE_SECURE=true` : cookies sécurisés sur HTTPS.

Limites : l'identifiant correspond à un navigateur/profil, pas à une personne réelle. Effacer les cookies, utiliser la navigation privée ou changer de navigateur peut créer un nouvel identifiant. Le User-Agent donne une indication sur le navigateur et parfois le système, mais ne permet pas de connaître avec certitude le nom physique de l'appareil. Aucun historique d'adresse IP n'est conservé. Les notes encore présentes uniquement dans `localStorage` ne seront importées que depuis le navigateur qui les possède.

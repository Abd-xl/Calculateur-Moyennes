# Journal de construction

## 2026-09-26 — Initialisation

Le dépôt de départ contient main.py, gestion_note.py, sauvegarde.py et README.md. Le programme fonctionne en terminal et utilise notes.json.

### Décision
Conserver la base Python et construire une interface web autour d'elle.

### Branche
web-app

### Prochaine étape
Créer le socle Flask sans modifier encore la logique de gestion des notes.

Le projet est construit étape par étape afin que chaque modification soit comprise avant de passer à la suivante.

## 2026-09-26 — Socle Flask + Jinja

### Ce qui a été ajouté
- `app.py` : crée l'application Flask et la route `/`.
- `templates/index.html` : première page HTML rendue par Flask avec `render_template()`.

### Compréhension
Le navigateur demande `/` → Flask exécute `accueil()` → `render_template("index.html")` charge le fichier dans `templates/` → Flask renvoie le HTML au navigateur.

Aucune logique de notes n'a encore été modifiée.

### Prochaine étape
Faire passer une première donnée Python vers Jinja avec une variable, puis l'afficher dans la page avec `{{ ... }}`.

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


## 2026-09-26 — Première réutilisation du cœur Python

### Ce qui a changé
- Une fonction `ajouter_note(matiere, note)` a été extraite de `gestion_note.py`.
- Cette fonction ne demande plus de `input()` et ne fait pas de `print()` : elle reçoit des données et les ajoute à la structure existante.
- `app.py` importe maintenant cette fonction ainsi que `notes`.
- Flask utilise donc les mêmes données que le reste du programme au lieu de conserver son propre dictionnaire de démonstration.

### Architecture
Le formulaire web → Flask → `ajouter_note()` → `notes` → sauvegarde JSON.

### Point important
Nous avons commencé à séparer l'interface de la logique métier. `gestion_note.py` peut progressivement devenir indépendant du terminal.

### Prochaine étape
Améliorer la validation des données reçues par Flask, puis utiliser correctement les coefficients et la structure réelle du calculateur.


## 2026-09-26 — Formulaire matière + coefficient + note

### Ce qui a changé
- Le formulaire web reçoit maintenant une matière, un coefficient et une note.
- `ajouter_note()` accepte ces trois données.
- Si la matière n'existe pas, elle est créée avec son coefficient.
- Si elle existe déjà, son coefficient doit rester identique.
- Les notes sont toujours enregistrées via `sauvegarder()`.

### Flux
Formulaire HTML → POST → `request.form` → conversion des types → `ajouter_note()` → `notes` / `coef` → JSON.

### Compréhension
Flask est responsable de recevoir et convertir les données du formulaire. La logique de validation et de modification des données commence à vivre dans `gestion_note.py`.

### Prochaine étape
Calculer et afficher les moyennes depuis les vraies données, puis supprimer progressivement les données de démonstration.


## 2026-09-26 — Calcul des moyennes dans la couche métier

### Ce qui a changé
- Extraction de `calculer_moyennes()` dans `gestion_note.py`.
- La fonction calcule la moyenne de chaque matière et la moyenne générale pondérée par les coefficients.
- `app.py` appelle cette fonction et transmet les résultats à Jinja.
- Jinja affiche les moyennes sans effectuer lui-même les calculs.

### Architecture
Données → fonctions Python de calcul → Flask → Jinja → HTML.

### Compréhension
Le HTML est responsable de l'affichage. Les calculs restent en Python : cela évite de mélanger la logique métier avec la présentation.

### Prochaine étape
Tester et renforcer le chargement des données, puis améliorer progressivement l'interface et les opérations de modification/suppression.

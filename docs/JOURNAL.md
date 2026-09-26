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

## 2026-09-26 — Chargement des données au démarrage

### Problème
`app.py` appelait `charger()` à chaque requête HTTP. Comme les dictionnaires sont conservés en mémoire et que `charger()` utilisait `update()`, cela pouvait réinjecter des données inutilement.

### Correction
- `charger()` est maintenant appelé une fois au démarrage de l'application Flask.
- Les cas de fichier absent ou de JSON invalide sont traités en repartant d'un état vide.

### Compréhension
Une requête HTTP ne doit pas reconstruire inutilement l'état de l'application. Pour cette première architecture, les données sont chargées au démarrage puis modifiées en mémoire et sauvegardées lorsque nécessaire.

### Limite connue
Cette architecture avec des variables globales et un fichier JSON reste adaptée à un petit projet local. Elle devra évoluer vers une vraie couche de persistance, probablement SQLite puis PostgreSQL, lorsque le projet deviendra plus sérieux ou multi-utilisateur.

## 2026-09-26 — Suppression d'une note depuis le Web

### Ce qui a changé
- Ajout de `supprimer_note(matiere, note)` dans `gestion_note.py`.
- Le formulaire d'ajout et les formulaires de suppression utilisent maintenant POST avec un champ `action`.
- Chaque note affichée possède un bouton de suppression.
- La suppression passe par la même logique métier que le reste du programme et déclenche la sauvegarde JSON.

### Compréhension
Un formulaire HTML peut envoyer différentes actions à la même route. Flask lit `request.form["action"]` pour savoir quelle opération effectuer, puis appelle la fonction Python correspondante.

### Prochaine étape
Ajouter la suppression d'une matière, puis aborder la modification d'une note.

## 2026-09-26 — Suppression d'une matière depuis le Web

### Ce qui a changé
- Ajout de `supprimer_matiere(matiere)` dans `gestion_note.py`.
- La fonction supprime les notes de la matière et son coefficient.
- Flask reconnaît maintenant l'action `supprimer_matiere`.
- Un bouton permet de supprimer chaque matière depuis la page.

### Point important
Une matière est représentée par deux structures liées : `notes[matiere]` et `coef[matiere]`. Les deux doivent être supprimées ensemble pour conserver un état cohérent.

### Prochaine étape
Implémenter la modification d'une note avec un formulaire Web.

## 2026-09-26 — Modification d'une note depuis le Web

### Ce qui a changé
- Ajout de `modifier_note(matiere, ancienne_note, nouvelle_note)`.
- La fonction vérifie la matière, l'existence de l'ancienne note et la validité de la nouvelle note.
- Le formulaire Web transmet l'ancienne et la nouvelle valeur.
- La note est remplacée dans la liste puis sauvegardée.

### Compréhension
Pour modifier une valeur dans une liste, il faut d'abord identifier l'ancienne valeur. Python utilise son index pour remplacer uniquement cette occurrence.

### Prochaine étape
Faire un premier nettoyage de l'architecture web, notamment séparer les routes/actions et préparer une interface plus adaptée à l'iPhone.

## 2026-09-26 — Nettoyage de `gestion_note.py`

### Problème trouvé
La fonction `supprimer_matiere()` existait deux fois. En Python, la deuxième définition remplace la première. La version destinée au Web était donc écrasée par l'ancienne version qui demandait des `input()`.

C'était un vrai risque : l'appel de Flask à `supprimer_matiere(matiere)` pouvait donc utiliser une fonction prévue pour le terminal.

### Correction
- Conservation d'une seule fonction métier `supprimer_matiere(matiere)`.
- Renommage de l'ancienne interface terminal en `menu_supprimer_matiere()`.
- `supprimer_notes()` utilise maintenant `supprimer_note()` au lieu de modifier directement les listes.
- `ajouter_notes()` utilise maintenant `ajouter_note()` au lieu de dupliquer la logique de validation et de sauvegarde.
- `voir_moyenne()` réutilise maintenant `calculer_moyennes()`.
- L'ancien menu terminal peut maintenant utiliser les mêmes fonctions métier que l'interface Web.
- L'option de modification d'une note du menu terminal appelle désormais `modifier_note()`.

### Architecture actuelle

```
Interface Web ──┐
                ├──> fonctions métier de gestion_note.py ──> sauvegarde.py ──> notes.json
Interface terminal ┘
```

### Compréhension
Une même opération métier ne doit pas être réécrite pour chaque interface. Le Web et le terminal peuvent appeler la même fonction Python, ce qui réduit les bugs et évite que deux versions du programme divergent.

### Prochaine étape
Séparer les actions Web en routes Flask dédiées, puis préparer l'interface responsive.

## 2026-09-26 — Routes Flask dédiées

### Problème
La route `/` recevait à la fois l'affichage de la page et toutes les actions POST. Un champ caché `action` permettait de choisir entre plusieurs blocs `if/elif`.

### Correction
Les actions Web ont maintenant chacune leur propre route :
- `GET /` : affiche la page.
- `POST /ajouter` : ajoute une note.
- `POST /modifier` : modifie une note.
- `POST /supprimer` : supprime une note.
- `POST /supprimer-matiere` : supprime une matière.

Les formulaires HTML utilisent directement l'attribut `action` correspondant à leur route.

### Nouveau concept : POST → Redirect → GET
Après une opération réussie, Flask redirige vers `/` avec un message.

Cela évite qu'un simple rechargement de la page renvoie une nouvelle fois le même formulaire POST. C'est un modèle courant des applications Web appelé **POST-Redirect-GET (PRG)**.

### Rôle de `afficher_page()`
La fonction `afficher_page()` prépare les moyennes et appelle `render_template()`. Les différentes routes peuvent donc réutiliser le même code d'affichage sans le recopier.

### Architecture actuelle

```
Navigateur
    ↓
Routes Flask
    ↓
Fonctions métier
    ↓
sauvegarde.py
    ↓
notes.json
```

### Prochaine étape
Tester toutes les actions après ce changement, puis commencer le CSS responsive pour l'utilisation sur iPhone.


## 2026-09-26 — Première structure de l'interface cible

### Objectif
Adapter la page d'accueil à la maquette définie pour l'application.

### Ce qui a changé
- La moyenne générale est placée en tête de page.
- Ajout de trois accès principaux :
  - ajouter une note ;
  - remplir le tableur ;
  - afficher toutes les notes.
- Les matières sont maintenant présentées dans un tableau avec :
  - matière ;
  - moyenne ;
  - coefficient ;
  - gestion.
- Cliquer sur une matière permet d'afficher ses notes avec l'élément HTML `details`.
- Création des pages `ajouter.html`, `notes.html` et `tableur.html`.
- `app.py` possède maintenant les routes GET correspondantes.

### Décision
La page d'accueil sert principalement de tableau de bord. Les opérations de saisie et les vues détaillées sont progressivement déplacées vers des pages dédiées.

### Prochaine étape
Définir précisément le fonctionnement du « Remplir le tableur », puis commencer le CSS responsive.


## 2026-09-26 — Tableau fixe et gestion des notes séparée

### Problème
L'affichage des notes avec `details` directement dans une ligne du tableau modifiait la hauteur de cette ligne et rendait le tableau visuellement instable.

### Correction
- Le tableau des matières reste maintenant compact et fixe.
- Le bouton « Modifier » ouvre une fenêtre `dialog` indépendante pour la matière.
- Les notes, leur modification et leur suppression sont gérées dans cette fenêtre sans modifier la structure du tableau.
- La suppression d'une matière reste disponible depuis cette fenêtre.

### Ordre de la page d'accueil
1. Tableau des matières.
2. « Remplir le tableur ».
3. Moyenne générale.
4. « Lister toutes les notes ».
5. « Ajouter une note ».

### Prochaine étape
Tester les actions de modification et de suppression depuis les fenêtres, puis commencer la mise en forme CSS.

## 2026-09-26 — Ajout de notes plus flexible

### Problèmes corrigés
- Une note pouvait uniquement être saisie sur 20.
- Ajouter une note à une matière existante obligeait à retaper son nom et son coefficient.
- Des espaces superflus pouvaient créer une matière visuellement identique.

### Correction
- Le formulaire permet de choisir une matière existante.
- Son coefficient est réutilisé automatiquement.
- Une section séparée permet de créer une nouvelle matière.
- Les barèmes /10 et /20 sont acceptés.
- Les notes sont normalisées sur /20 dans les données internes.
- Les espaces superflus et les différences de casse sont ignorés lors de la recherche d'une matière existante.

### Prochaine étape
Tester les nouveaux cas avant de poursuivre vers le tableur.



## 2026-09-26 — Conservation du barème original

### Correction
- Les notes ne sont plus converties et stockées directement sur /20.
- Chaque note conserve maintenant sa valeur et son barème d'origine, par exemple `10/10` ou `15/20`.
- La conversion sur /20 est effectuée uniquement au moment du calcul de la moyenne.
- La modification et la suppression utilisent l'index de la note afin de distinguer deux notes ayant la même valeur.

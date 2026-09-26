# Architecture

## Actuelle
main.py -> interface terminal -> gestion_note.py -> sauvegarde.py -> notes.json

gestion_note.py contient actuellement à la fois la logique et l'interface terminal.

## Première architecture cible
Navigateur -> HTTP -> app.py (Flask) -> fonctions Python réutilisables -> sauvegarde.py -> notes.json

## Évolution
À terme : frontend -> Flask/API -> logique métier -> persistance -> SQLite/PostgreSQL.

On ne met pas toute cette architecture en place d'un coup.
from flask import Flask, render_template, request
from gestion_note import ajouter_note, calculer_moyennes, supprimer_matiere, supprimer_note, notes, coef
from sauvegarde import charger

app = Flask(__name__)
charger()


@app.route("/", methods=["GET", "POST"])
def accueil():
    message = None

    if request.method == "POST":
        action = request.form.get("action")

        try:
            if action == "ajouter":
                matiere = request.form["matiere"]
                note = float(request.form["note"])
                coefficient = int(request.form["coefficient"])
                ajouter_note(matiere, note, coefficient)
                message = f"Note ajoutée : {matiere} — {note}/20"

            elif action == "supprimer":
                matiere = request.form["matiere"]
                note = float(request.form["note"])
                supprimer_note(matiere, note)
                message = f"Note supprimée : {matiere} — {note}/20"

            elif action == "supprimer_matiere":
                matiere = request.form["matiere"]
                supprimer_matiere(matiere)
                message = f"Matière supprimée : {matiere}"

        except (TypeError, ValueError) as erreur:
            message = str(erreur)

    moyennes, moyenne_generale = calculer_moyennes()

    return render_template(
        "index.html",
        notes=notes,
        coef=coef,
        moyennes=moyennes,
        moyenne_generale=moyenne_generale,
        message=message
    )


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request
from gestion_note import ajouter_note, notes, coef
from sauvegarde import charger

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def accueil():
    charger()
    message = None

    if request.method == "POST":
        matiere = request.form["matiere"]

        try:
            note = float(request.form["note"])
            coefficient = int(request.form["coefficient"])
            ajouter_note(matiere, note, coefficient)
            message = f"Note ajoutée : {matiere} — {note}/20"
        except (TypeError, ValueError) as erreur:
            message = str(erreur)

    return render_template(
        "index.html",
        notes=notes,
        coef=coef,
        message=message
    )


if __name__ == "__main__":
    app.run(debug=True)

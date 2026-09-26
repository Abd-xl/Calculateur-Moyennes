from flask import Flask, render_template, request, redirect, url_for
from gestion_note import (
    ajouter_note,
    calculer_moyennes,
    modifier_note,
    supprimer_matiere,
    supprimer_note,
    notes,
    coef,
)
from sauvegarde import charger

app = Flask(__name__)
charger()


def afficher_page(message=None):
    moyennes, moyenne_generale = calculer_moyennes()

    return render_template(
        "index.html",
        notes=notes,
        coef=coef,
        moyennes=moyennes,
        moyenne_generale=moyenne_generale,
        message=message,
    )


@app.route("/")
def accueil():
    message = request.args.get("message")
    return afficher_page(message)


@app.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    if request.method == "GET":
        return render_template("ajouter.html")

    try:
        matiere = request.form["matiere"]
        note = float(request.form["note"])
        coefficient = int(request.form["coefficient"])

        ajouter_note(matiere, note, coefficient)

        message = f"Note ajoutée : {matiere} — {note}/20"
        return redirect(url_for("accueil", message=message))

    except (TypeError, ValueError) as erreur:
        return render_template("ajouter.html", message=str(erreur))


@app.route("/notes")
def liste_notes():
    return render_template("notes.html", notes=notes, coef=coef)


@app.route("/tableur")
def tableur():
    return render_template("tableur.html", notes=notes, coef=coef)


@app.route("/supprimer", methods=["POST"])
def supprimer():
    try:
        matiere = request.form["matiere"]
        note = float(request.form["note"])

        supprimer_note(matiere, note)

        message = f"Note supprimée : {matiere} — {note}/20"
        return redirect(url_for("accueil", message=message))

    except (TypeError, ValueError) as erreur:
        return afficher_page(str(erreur))


@app.route("/modifier", methods=["POST"])
def modifier():
    try:
        matiere = request.form["matiere"]
        ancienne_note = float(request.form["ancienne_note"])
        nouvelle_note = float(request.form["nouvelle_note"])

        modifier_note(matiere, ancienne_note, nouvelle_note)

        message = (
            f"Note modifiée : {matiere} — "
            f"{ancienne_note} → {nouvelle_note}/20"
        )
        return redirect(url_for("accueil", message=message))

    except (TypeError, ValueError) as erreur:
        return afficher_page(str(erreur))


@app.route("/supprimer-matiere", methods=["POST"])
def supprimer_matiere_route():
    try:
        matiere = request.form["matiere"]

        supprimer_matiere(matiere)

        message = f"Matière supprimée : {matiere}"
        return redirect(url_for("accueil", message=message))

    except (TypeError, ValueError) as erreur:
        return afficher_page(str(erreur))


if __name__ == "__main__":
    app.run(debug=True)

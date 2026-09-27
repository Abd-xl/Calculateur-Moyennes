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
from sauvegarde import DonneesInvalidesError, SauvegardeError, charger

app = Flask(__name__)

erreur_chargement = None

try:
    charger()
except DonneesInvalidesError as erreur:
    erreur_chargement = str(erreur)


def afficher_page(message=None):
    moyennes, moyenne_generale = calculer_moyennes()

    return render_template(
        "index.html",
        notes=notes,
        coef=coef,
        moyennes=moyennes,
        moyenne_generale=moyenne_generale,
        message=message,
        erreur_chargement=erreur_chargement,
    )


@app.route("/")
def accueil():
    message = request.args.get("message")
    return afficher_page(message)


@app.route("/chargement/reessayer", methods=["POST"])
def reessayer_chargement():
    global erreur_chargement

    try:
        charger()
        erreur_chargement = None
        message = "Données chargées avec succès."
    except DonneesInvalidesError as erreur:
        erreur_chargement = str(erreur)
        message = "Le fichier notes.json est toujours invalide."

    return redirect(url_for("accueil", message=message))


@app.route("/chargement/vide", methods=["POST"])
def utiliser_donnees_vides():
    global erreur_chargement

    notes.clear()
    coef.clear()
    erreur_chargement = None

    return redirect(
        url_for(
            "accueil",
            message=(
                "Données vides utilisées. Le fichier notes.json "
                "existant n'a pas été supprimé."
            ),
        )
    )


@app.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    if request.method == "GET":
        return render_template("ajouter.html", notes=notes, coef=coef)

    try:
        mode = request.form["mode"]
        note = float(request.form["note"])
        bareme = int(request.form["bareme"])

        if mode == "existante":
            matiere = request.form["matiere_existante"]
            coefficient = coef[matiere]
        elif mode == "nouvelle":
            matiere = request.form["nouvelle_matiere"]
            coefficient = int(request.form["coefficient"])
        else:
            raise ValueError("Mode invalide.")

        ajouter_note(matiere, note, coefficient, bareme)

        note_sur_20 = note * 20 / bareme
        message = f"Note ajoutée : {matiere} — {note:g}/{bareme} ({note_sur_20:g}/20)"
        return redirect(url_for("accueil", message=message))

    except SauvegardeError as erreur:
        return render_template(
            "ajouter.html",
            notes=notes,
            coef=coef,
            message=str(erreur),
        )

    except (KeyError, TypeError, ValueError) as erreur:
        return render_template(
            "ajouter.html",
            notes=notes,
            coef=coef,
            message=str(erreur),
        )


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
        index = int(request.form["index"])
        note = notes[matiere][index]

        supprimer_note(matiere, index)

        message = (
            f"Note supprimée : {matiere} — "
            f"{note['note']:g}/{note['bareme']}"
        )
        return redirect(url_for("accueil", message=message))

    except SauvegardeError as erreur:
        return afficher_page(str(erreur))

    except (KeyError, IndexError, TypeError, ValueError) as erreur:
        return afficher_page(str(erreur))


@app.route("/modifier", methods=["POST"])
def modifier():
    try:
        matiere = request.form["matiere"]
        index = int(request.form["index"])
        nouvelle_note = float(request.form["nouvelle_note"])

        modifier_note(matiere, index, nouvelle_note)

        message = f"Note modifiée : {matiere} — {nouvelle_note:g}"
        return redirect(url_for("accueil", message=message))

    except SauvegardeError as erreur:
        return afficher_page(str(erreur))

    except (KeyError, TypeError, ValueError) as erreur:
        return afficher_page(str(erreur))


@app.route("/supprimer-matiere", methods=["POST"])
def supprimer_matiere_route():
    try:
        matiere = request.form["matiere"]

        supprimer_matiere(matiere)

        message = f"Matière supprimée : {matiere}"
        return redirect(url_for("accueil", message=message))

    except SauvegardeError as erreur:
        return afficher_page(str(erreur))

    except (KeyError, TypeError, ValueError) as erreur:
        return afficher_page(str(erreur))


if __name__ == "__main__":
    app.run(debug=True)

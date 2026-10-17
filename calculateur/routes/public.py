"""Routes publiques du calculateur et API de synchronisation."""
from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from domaine import (
    DonneesInvalidesError,
    ajouter_note_donnees,
    calculer_moyennes,
    modifier_note_donnees,
    supprimer_matiere_donnees,
    supprimer_note_donnees,
)
from ..extensions import db
from ..services import current_data, save_data


public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def accueil():
    data = current_data()
    moyennes, moyenne_generale = calculer_moyennes(data["notes"], data["coef"])
    return render_template(
        "index.html",
        notes=data["notes"],
        coef=data["coef"],
        moyennes=moyennes,
        moyenne_generale=moyenne_generale,
        message=request.args.get("message"),
    )


@public_bp.route("/api/etat")
def etat_api():
    response = jsonify(current_data())
    response.headers["Cache-Control"] = "no-store"
    return response


@public_bp.route("/api/synchroniser", methods=["POST"])
def synchroniser_api():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Données invalides."}), 400
    try:
        save_data(data)
    except (DonneesInvalidesError, TypeError) as erreur:
        db.session.rollback()
        return jsonify({"error": str(erreur)}), 400

    response = jsonify(current_data())
    response.headers["Cache-Control"] = "no-store"
    return response


@public_bp.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    data = current_data()
    if request.method == "GET":
        return render_template(
            "ajouter.html",
            notes=data["notes"],
            coef=data["coef"],
        )

    try:
        mode = request.form["mode"]
        note = float(request.form["note"])
        bareme = int(request.form["bareme"])

        if mode == "existante":
            matiere = request.form["matiere_existante"]
            if matiere not in data["coef"]:
                raise ValueError("Matière inconnue.")
            coefficient = data["coef"][matiere]
        elif mode == "nouvelle":
            matiere = request.form["nouvelle_matiere"]
            coefficient = int(request.form["coefficient"])
        else:
            raise ValueError("Mode invalide.")

        matiere, _created = ajouter_note_donnees(
            data, matiere, note, coefficient, bareme
        )
        save_data(data)
        return redirect(url_for(
            "public.accueil",
            message=f"Note ajoutée : {matiere} — {note:g}/{bareme}",
        ))
    except (KeyError, TypeError, ValueError, DonneesInvalidesError) as erreur:
        db.session.rollback()
        latest = current_data()
        return render_template(
            "ajouter.html",
            notes=latest["notes"],
            coef=latest["coef"],
            message=str(erreur),
        ), 400


@public_bp.route("/notes")
def liste_notes():
    data = current_data()
    return render_template("notes.html", notes=data["notes"], coef=data["coef"])


@public_bp.route("/tableur")
def tableur():
    data = current_data()
    return render_template("tableur.html", notes=data["notes"], coef=data["coef"])


@public_bp.route("/supprimer", methods=["POST"])
def supprimer():
    data = current_data()
    try:
        matiere = request.form["matiere"]
        index = int(request.form["index"])
        supprimer_note_donnees(data, matiere, index)
        save_data(data)
        message = "Note supprimée."
    except (KeyError, TypeError, ValueError) as erreur:
        db.session.rollback()
        message = f"Suppression impossible : {erreur}"
    return redirect(url_for("public.accueil", message=message))


@public_bp.route("/modifier", methods=["POST"])
def modifier():
    data = current_data()
    try:
        matiere = request.form["matiere"]
        index = int(request.form["index"])
        nouvelle_note = float(request.form["nouvelle_note"])
        modifier_note_donnees(data, matiere, index, nouvelle_note)
        save_data(data)
        message = "Note mise à jour."
    except (KeyError, TypeError, ValueError) as erreur:
        db.session.rollback()
        message = f"Modification impossible : {erreur}"
    return redirect(url_for("public.accueil", message=message))


@public_bp.route("/supprimer-matiere", methods=["POST"])
def supprimer_matiere_route():
    data = current_data()
    try:
        matiere = request.form["matiere"]
        supprimer_matiere_donnees(data, matiere)
        save_data(data)
        message = "Matière supprimée."
    except (KeyError, TypeError, ValueError) as erreur:
        db.session.rollback()
        message = f"Suppression de la matière impossible : {erreur}"
    return redirect(url_for("public.accueil", message=message))

"""Routes publiques du calculateur."""

import copy

from flask import g, jsonify, redirect, render_template, request, url_for

from calculateur.extensions import db
from calculateur.services.gradebook import add_note, delete_note, delete_subject, modify_note
from calculateur.services.grades import calculate_averages
from calculateur.services.validation import DonneesInvalidesError, validate_data


def _current_data():
    return copy.deepcopy(g.visitor.data or {"notes": {}, "coef": {}})


def _save_data(data):
    validate_data(data)
    g.visitor.data = copy.deepcopy(data)
    g.visitor.data_initialized = True
    db.session.commit()


def register_public_routes(app):
    @app.route("/")
    def accueil():
        data = _current_data()
        moyennes, moyenne_generale = calculate_averages(data)
        return render_template(
            "index.html", notes=data["notes"], coef=data["coef"], moyennes=moyennes,
            moyenne_generale=moyenne_generale, message=request.args.get("message"),
            erreur_chargement=None,
        )

    @app.route("/api/etat")
    def etat_api():
        response = jsonify(_current_data())
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.route("/api/synchroniser", methods=["POST"])
    def synchroniser_api():
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "Données invalides."}), 400
        try:
            _save_data(data)
        except (DonneesInvalidesError, TypeError) as erreur:
            db.session.rollback()
            return jsonify({"error": str(erreur)}), 400
        response = jsonify(_current_data())
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.route("/ajouter", methods=["GET", "POST"])
    def ajouter():
        data = _current_data()
        notes, coef = data["notes"], data["coef"]
        if request.method == "GET":
            return render_template("ajouter.html", notes=notes, coef=coef)
        try:
            mode = request.form["mode"]
            note = float(request.form["note"])
            bareme = int(request.form["bareme"])
            if mode == "existante":
                matiere = request.form["matiere_existante"]
                if matiere not in coef:
                    raise ValueError("Matière inconnue.")
                coefficient = coef[matiere]
            elif mode == "nouvelle":
                matiere = request.form["nouvelle_matiere"].strip()
                coefficient = int(request.form["coefficient"])
            else:
                raise ValueError("Mode invalide.")
            matiere = add_note(data, matiere, note, coefficient, bareme)
            _save_data(data)
            return redirect(url_for("accueil", message=f"Note ajoutée : {matiere} — {note:g}/{bareme}"))
        except (KeyError, TypeError, ValueError, DonneesInvalidesError) as erreur:
            db.session.rollback()
            data = _current_data()
            return render_template(
                "ajouter.html", notes=data["notes"], coef=data["coef"], message=str(erreur)
            ), 400

    @app.route("/notes")
    def liste_notes():
        data = _current_data()
        return render_template("notes.html", notes=data["notes"], coef=data["coef"])

    @app.route("/tableur")
    def tableur():
        data = _current_data()
        return render_template("tableur.html", notes=data["notes"], coef=data["coef"])

    @app.route("/supprimer", methods=["POST"])
    def supprimer():
        data = _current_data()
        try:
            delete_note(data, request.form["matiere"], int(request.form["index"]))
            _save_data(data)
        except (KeyError, IndexError, TypeError, ValueError, DonneesInvalidesError):
            db.session.rollback()
        return redirect(url_for("accueil"))

    @app.route("/modifier", methods=["POST"])
    def modifier():
        data = _current_data()
        try:
            nouvelle_note = float(request.form["nouvelle_note"])
            modify_note(data, request.form["matiere"], int(request.form["index"]), nouvelle_note)
            _save_data(data)
        except (KeyError, IndexError, TypeError, ValueError, DonneesInvalidesError):
            db.session.rollback()
        return redirect(url_for("accueil"))

    @app.route("/supprimer-matiere", methods=["POST"])
    def supprimer_matiere_route():
        data = _current_data()
        try:
            delete_subject(data, request.form["matiere"])
            _save_data(data)
        except (KeyError, TypeError, ValueError, DonneesInvalidesError):
            db.session.rollback()
        return redirect(url_for("accueil"))

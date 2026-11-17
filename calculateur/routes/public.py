"""Routes publiques du calculateur."""

from flask import current_app, g, jsonify, redirect, render_template, request, url_for

from calculateur.repositories.memory_gradebook import GradebookConflictError
from calculateur.services.gradebook import add_note, delete_note, delete_subject, modify_note
from calculateur.services.grades import calculate_averages
from calculateur.services.validation import DonneesInvalidesError


def _repository():
    return current_app.extensions["gradebook_repository"]


def _current_profile():
    return _repository().load(g.profile_id)


def _current_data():
    return _current_profile()["data"]


def _expected_version():
    value = request.headers.get("If-Match") or request.form.get("_version")
    if value is None:
        # Compatibilité avec les anciens clients API.
        return g.visitor.gradebook_version
    try:
        return int(value.strip().strip('"'))
    except (AttributeError, ValueError) as error:
        raise ValueError("Version de synchronisation invalide.") from error


def _save_data(data):
    version = _repository().save(g.profile_id, data, _expected_version())
    g.visitor.data_initialized = True
    g.visitor.gradebook_version = version
    return version


def _conflict_response():
    profile = _current_profile()
    response = jsonify(
        {
            "error": "version_conflict",
            "message": "Les données ont changé dans une autre requête. Rechargez-les avant de réessayer.",
            "data": profile["data"],
            "version": profile["version"],
        }
    )
    response.status_code = 409
    response.headers["ETag"] = f'"{profile["version"]}"'
    response.headers["Cache-Control"] = "no-store"
    return response


def register_public_routes(app):
    @app.route("/")
    def accueil():
        data = _current_data()
        moyennes, moyenne_generale = calculate_averages(data)
        return render_template(
            "index.html",
            notes=data["notes"],
            coef=data["coef"],
            moyennes=moyennes,
            moyenne_generale=moyenne_generale,
            message=request.args.get("message"),
            erreur_chargement=None,
        )

    @app.route("/api/etat")
    def etat_api():
        profile = _current_profile()
        response = jsonify(profile["data"])
        response.headers["Cache-Control"] = "no-store"
        response.headers["ETag"] = f'"{profile["version"]}"'
        return response

    @app.route("/api/synchroniser", methods=["POST"])
    def synchroniser_api():
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "Données invalides."}), 400
        try:
            _save_data(data)
        except GradebookConflictError:
            return _conflict_response()
        except (DonneesInvalidesError, TypeError, ValueError) as erreur:
            return jsonify({"error": str(erreur)}), 400

        profile = _current_profile()
        response = jsonify(profile["data"])
        response.headers["Cache-Control"] = "no-store"
        response.headers["ETag"] = f'"{profile["version"]}"'
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
        except GradebookConflictError:
            return _conflict_response()
        except (KeyError, TypeError, ValueError, DonneesInvalidesError) as erreur:
            profile = _current_profile()
            g.visitor.data_initialized = profile["initialized"]
            g.visitor.gradebook_version = profile["version"]
            data = profile["data"]
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
        except GradebookConflictError:
            return _conflict_response()
        except (KeyError, IndexError, TypeError, ValueError, DonneesInvalidesError):
            pass
        return redirect(url_for("accueil"))

    @app.route("/modifier", methods=["POST"])
    def modifier():
        data = _current_data()
        try:
            nouvelle_note = float(request.form["nouvelle_note"])
            modify_note(data, request.form["matiere"], int(request.form["index"]), nouvelle_note)
            _save_data(data)
        except GradebookConflictError:
            return _conflict_response()
        except (KeyError, IndexError, TypeError, ValueError, DonneesInvalidesError):
            pass
        return redirect(url_for("accueil"))

    @app.route("/supprimer-matiere", methods=["POST"])
    def supprimer_matiere_route():
        data = _current_data()
        try:
            delete_subject(data, request.form["matiere"])
            _save_data(data)
        except GradebookConflictError:
            return _conflict_response()
        except (KeyError, TypeError, ValueError, DonneesInvalidesError):
            pass
        return redirect(url_for("accueil"))

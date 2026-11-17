"""Point d'information conservé après la désactivation de l'administration."""

from flask import make_response, render_template


def register_admin_routes(app):
    @app.route("/admin", methods=["GET"])
    def admin_dashboard():
        # La page reste présente pour expliquer la désactivation, mais aucune
        # authentification, lecture de profil, suppression ou export n'est exposé.
        response = make_response(render_template("admin.html"), 503)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

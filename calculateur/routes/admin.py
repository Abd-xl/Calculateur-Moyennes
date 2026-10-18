"""Routes de connexion et de consultation administrateur."""

import hmac
import io
import json
import os

from flask import abort, flash, redirect, render_template, request, send_file, session, url_for

from calculateur.extensions import db, limiter
from calculateur.models import Visitor, utcnow
from calculateur.security import admin_required


def register_admin_routes(app):
    @app.route("/admin/connexion", methods=["GET", "POST"])
    @limiter.limit("5 per minute; 20 per hour", methods=["POST"])
    def admin_login():
        if session.get("admin_authenticated"):
            return redirect(url_for("admin_dashboard"))
        if request.method == "POST":
            expected_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
            expected_password = os.environ.get("ADMIN_PASSWORD", "")
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if expected_email and expected_password and hmac.compare_digest(email, expected_email) and hmac.compare_digest(password, expected_password):
                session.clear()
                session["admin_authenticated"] = True
                session.permanent = True
                return redirect(url_for("admin_dashboard"))
            flash("Identifiants administrateur incorrects ou non configurés.", "error")
        return render_template("admin_login.html")

    @app.route("/admin/deconnexion", methods=["POST"])
    @admin_required
    def admin_logout():
        session.clear()
        return redirect(url_for("admin_login"))

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        visitors = Visitor.query.order_by(Visitor.last_seen_at.desc()).all()
        return render_template("admin.html", users=visitors)

    @app.route("/admin/utilisateur/<int:user_id>")
    @admin_required
    def admin_user_detail(user_id):
        visitor = db.session.get(Visitor, user_id)
        if visitor is None:
            abort(404)
        return render_template(
            "admin_user.html", user=visitor, data=visitor.data or {"notes": {}, "coef": {}}
        )

    @app.route("/admin/export.json")
    @admin_required
    def admin_export():
        payload = {
            "exported_at": utcnow().isoformat(),
            "visitors": [
                {
                    "id": visitor.id,
                    "anonymous_id": visitor.public_id,
                    "browser_info": visitor.browser_info,
                    "created_at": visitor.created_at.isoformat() if visitor.created_at else None,
                    "last_seen_at": visitor.last_seen_at.isoformat() if visitor.last_seen_at else None,
                    "data": visitor.data or {"notes": {}, "coef": {}},
                }
                for visitor in Visitor.query.order_by(Visitor.id).all()
            ],
        }
        file = io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
        file.seek(0)
        return send_file(
            file, mimetype="application/json", as_attachment=True,
            download_name="export-visiteurs.json",
        )

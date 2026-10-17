"""Routes de l'espace administrateur."""
import hmac
import io
import json
import os

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, session, url_for

from ..extensions import db, limiter
from ..models import Visitor, utcnow
from ..security import admin_required
from ..services import EMPTY_DATA


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/connexion", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
def admin_login():
    if session.get("admin_authenticated"):
        return redirect(url_for("admin.admin_dashboard"))

    if request.method == "POST":
        expected_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
        expected_password = os.environ.get("ADMIN_PASSWORD", "")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if (
            expected_email
            and expected_password
            and hmac.compare_digest(email, expected_email)
            and hmac.compare_digest(password, expected_password)
        ):
            session.clear()
            session["admin_authenticated"] = True
            session.permanent = True
            return redirect(url_for("admin.admin_dashboard"))
        flash("Identifiants administrateur incorrects ou non configurés.", "error")

    return render_template("admin_login.html")


@admin_bp.route("/deconnexion", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin.admin_login"))


@admin_bp.route("")
@admin_required
def admin_dashboard():
    visitors = Visitor.query.order_by(Visitor.last_seen_at.desc()).all()
    return render_template("admin.html", users=visitors)


@admin_bp.route("/utilisateur/<int:user_id>")
@admin_required
def admin_user_detail(user_id):
    visitor = db.session.get(Visitor, user_id)
    if visitor is None:
        abort(404)
    return render_template(
        "admin_user.html",
        user=visitor,
        data=visitor.data or EMPTY_DATA,
    )


@admin_bp.route("/export.json")
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
                "data": visitor.data or EMPTY_DATA,
            }
            for visitor in Visitor.query.order_by(Visitor.id).all()
        ],
    }
    output = io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
    output.seek(0)
    return send_file(
        output,
        mimetype="application/json",
        as_attachment=True,
        download_name="export-visiteurs.json",
    )

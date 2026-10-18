"""Routes de connexion et de consultation administrateur."""

import hmac
import io
import json
import os

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import selectinload
from flask import abort, flash, redirect, render_template, request, send_file, session, url_for

from calculateur.extensions import db, limiter
from calculateur.models import Grade, Subject, Visitor, utcnow
from calculateur.repositories.visitor_gradebook import load_gradebook
from calculateur.security import admin_required

ADMIN_PAGE_SIZE = 25


def register_admin_routes(app):
    @app.after_request
    def prevent_admin_response_caching(response):
        if request.path.startswith("/admin"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

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
        search = request.args.get("q", "").strip()[:128]
        query = Visitor.query
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    cast(Visitor.id, String).ilike(pattern),
                    Visitor.public_id.ilike(pattern),
                    Visitor.browser_info.ilike(pattern),
                )
            )

        result_count = query.count()
        total_pages = max(1, (result_count + ADMIN_PAGE_SIZE - 1) // ADMIN_PAGE_SIZE)
        page = min(max(request.args.get("page", 1, type=int) or 1, 1), total_pages)
        visitors = (
            query.order_by(Visitor.last_seen_at.desc(), Visitor.id.desc())
            .limit(ADMIN_PAGE_SIZE)
            .offset((page - 1) * ADMIN_PAGE_SIZE)
            .all()
        )

        totals = db.session.execute(
            select(
                select(func.count()).select_from(Visitor).scalar_subquery(),
                select(func.count()).select_from(Subject).scalar_subquery(),
                select(func.count()).select_from(Grade).scalar_subquery(),
            )
        ).one()

        visitor_stats = {}
        visitor_ids = [visitor.id for visitor in visitors]
        if visitor_ids:
            rows = db.session.execute(
                select(
                    Subject.visitor_id,
                    func.count(func.distinct(Subject.id)),
                    func.count(Grade.id),
                )
                .outerjoin(Grade, Grade.subject_id == Subject.id)
                .where(Subject.visitor_id.in_(visitor_ids))
                .group_by(Subject.visitor_id)
            )
            visitor_stats = {
                visitor_id: {"subjects": subject_count, "grades": grade_count}
                for visitor_id, subject_count, grade_count in rows
            }

        return render_template(
            "admin.html",
            users=visitors,
            visitor_stats=visitor_stats,
            total_visitors=totals[0],
            total_subjects=totals[1],
            total_notes=totals[2],
            result_count=result_count,
            page=page,
            total_pages=total_pages,
            search=search,
        )

    @app.route("/admin/utilisateur/<int:user_id>")
    @admin_required
    def admin_user_detail(user_id):
        visitor = db.session.get(Visitor, user_id)
        if visitor is None:
            abort(404)
        return render_template(
            "admin_user.html", user=visitor, data=load_gradebook(visitor)
        )

    @app.route("/admin/utilisateur/<int:user_id>/supprimer", methods=["POST"])
    @admin_required
    def admin_delete_visitor(user_id):
        visitor = db.session.get(Visitor, user_id)
        if visitor is None:
            abort(404)
        db.session.delete(visitor)
        db.session.commit()
        flash(f"Le profil visiteur #{user_id} et ses données ont été supprimés.", "success")
        return redirect(url_for("admin_dashboard"))

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
                    "data": load_gradebook(visitor),
                }
                for visitor in db.session.scalars(
                    select(Visitor)
                    .options(selectinload(Visitor.subjects).selectinload(Subject.grades))
                    .order_by(Visitor.id)
                )
            ],
        }
        file = io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
        file.seek(0)
        return send_file(
            file, mimetype="application/json", as_attachment=True,
            download_name="export-visiteurs.json",
        )

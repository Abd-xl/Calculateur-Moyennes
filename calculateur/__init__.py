"""Fabrique Flask et assemblage de l'application web."""
import os
from pathlib import Path

from flask import Flask, render_template
from flask_wtf.csrf import generate_csrf

from .extensions import csrf, db, limiter
from .security import register_browser_hooks


def create_app(test_config=None):
    """Construit une application configurable, notamment pour les tests."""
    secret_key = os.environ.get("SECRET_KEY")
    if os.environ.get("RENDER") == "true" and not secret_key:
        raise RuntimeError("Configure SECRET_KEY dans Render.")

    database_url = os.environ.get("DATABASE_URL", "sqlite:///calculateur.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app_config = {
        "SECRET_KEY": secret_key or "development-only-change-this-secret",
        "SQLALCHEMY_DATABASE_URI": database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": os.environ.get(
            "COOKIE_SECURE",
            "true" if os.environ.get("RENDER") == "true" else "false",
        ).lower() == "true",
        "PERMANENT_SESSION_LIFETIME": 60 * 60 * 24 * 30,
        "RATELIMIT_STORAGE_URI": os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
        "MAX_CONTENT_LENGTH": 1024 * 1024,
    }

    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )
    app.config.update(app_config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    @app.context_processor
    def template_helpers():
        return {"csrf_token": generate_csrf}

    register_browser_hooks(app)

    from .routes.admin import admin_bp
    from .routes.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template(
            "error.html",
            code=403,
            message="Accès réservé à l’administrateur.",
        ), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template(
            "error.html",
            code=404,
            message="Visiteur introuvable.",
        ), 404

    # Compatibilité conservée. create_all crée les tables manquantes, mais ne migre pas.
    with app.app_context():
        db.create_all()

    return app


__all__ = ["create_app", "db"]

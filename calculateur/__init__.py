"""Application Flask et assemblage de ses extensions."""

import os


def _database_uri():
    uri = os.environ.get("DATABASE_URL", "sqlite:///calculateur.db")
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql+psycopg://", 1)
    if uri.startswith("postgresql://"):
        return uri.replace("postgresql://", "postgresql+psycopg://", 1)
    return uri


def create_app(test_config=None):
    """Construit l'application sans coupler les extensions à un seul contexte."""
    from pathlib import Path

    from flask import Flask, render_template
    from flask_wtf.csrf import generate_csrf

    from calculateur.cli import register_cli_commands
    from calculateur.extensions import csrf, db, limiter, migrate
    from calculateur.request_hooks import register_request_hooks
    from calculateur.routes.admin import register_admin_routes
    from calculateur.routes.public import register_public_routes

    secret = os.environ.get("SECRET_KEY")
    if os.environ.get("RENDER") == "true" and not secret:
        raise RuntimeError("Configure SECRET_KEY dans Render.")

    app = Flask(
        __name__,
        root_path=str(Path(__file__).resolve().parent.parent),
    )
    app.config.update(
        SECRET_KEY=secret or "development-only-change-this-secret",
        SQLALCHEMY_DATABASE_URI=_database_uri(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get(
            "COOKIE_SECURE", "true" if os.environ.get("RENDER") == "true" else "false"
        ).lower() == "true",
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db, compare_type=True)
    register_request_hooks(app)
    register_public_routes(app)
    register_admin_routes(app)
    register_cli_commands(app)

    @app.context_processor
    def template_helpers():
        return {"csrf_token": generate_csrf}

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="Accès réservé à l’administrateur."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="Visiteur introuvable."), 404

    # Test fixtures and local tools can opt in; deployments must use migrations.
    if app.config.get("AUTO_CREATE_DB"):
        with app.app_context():
            db.create_all()

    return app


__all__ = ["create_app"]

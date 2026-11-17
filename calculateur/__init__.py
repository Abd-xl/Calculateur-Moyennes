"""Fabrique de l'application Flask sans dépendance à une base de données."""

import os
from pathlib import Path


def create_app(test_config=None):
    from flask import Flask, render_template

    from calculateur.extensions import csrf
    from calculateur.repositories.memory_gradebook import InMemoryGradebookRepository
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
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=(
            os.environ.get(
                "COOKIE_SECURE",
                "true" if os.environ.get("RENDER") == "true" else "false",
            ).lower()
            == "true"
        ),
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30,
        MEMORY_PROFILE_LIMIT=1000,
    )
    if test_config:
        app.config.update(test_config)

    app.extensions["gradebook_repository"] = InMemoryGradebookRepository(
        max_profiles=app.config["MEMORY_PROFILE_LIMIT"]
    )

    csrf.init_app(app)
    register_request_hooks(app)
    register_public_routes(app)
    register_admin_routes(app)

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template(
            "error.html",
            code=403,
            message="Cette action n'est pas autorisée.",
        ), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template(
            "error.html",
            code=404,
            message="Cette page n'existe pas.",
        ), 404

    return app


__all__ = ["create_app"]

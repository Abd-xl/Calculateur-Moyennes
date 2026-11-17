"""Identifie le profil navigateur sans créer de donnée en base."""

import secrets
from types import SimpleNamespace

from flask import current_app, g, request, session


def register_request_hooks(app):
    @app.before_request
    def identify_browser():
        g.profile_id = None
        g.visitor = None

        if request.path.startswith(("/static/", "/admin")):
            return

        profile_id = session.get("gradebook_profile_id")
        if not profile_id:
            profile_id = secrets.token_urlsafe(32)
            session["gradebook_profile_id"] = profile_id

        session.permanent = True
        profile = current_app.extensions["gradebook_repository"].load(profile_id)
        g.profile_id = profile_id
        # Les templates existants utilisent encore ces deux attributs.
        g.visitor = SimpleNamespace(
            data_initialized=profile["initialized"],
            gradebook_version=profile["version"],
        )

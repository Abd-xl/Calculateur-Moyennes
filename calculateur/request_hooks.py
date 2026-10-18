"""Identification du profil anonyme associé à chaque requête."""

import secrets
import uuid

from flask import current_app, g, request

from calculateur.extensions import db
from calculateur.models import Visitor, utcnow
from calculateur.security import VISITOR_COOKIE, hash_token


def register_request_hooks(app):
    @app.before_request
    def identify_browser():
        g.visitor = None
        g.new_visitor_token = None
        if request.path.startswith("/admin") or request.path.startswith("/static/"):
            return

        token = request.cookies.get(VISITOR_COOKIE)
        visitor = Visitor.query.filter_by(token_hash=hash_token(token)).first() if token else None
        if visitor is None:
            token = secrets.token_urlsafe(32)
            visitor = Visitor(
                public_id=uuid.uuid4().hex,
                token_hash=hash_token(token),
                browser_info=request.user_agent.string[:512] or "Inconnu",
                data={"notes": {}, "coef": {}},
            )
            db.session.add(visitor)
            db.session.commit()
            g.new_visitor_token = token
        else:
            visitor.last_seen_at = utcnow()
            visitor.browser_info = request.user_agent.string[:512] or visitor.browser_info
            db.session.commit()
        g.visitor = visitor

    @app.after_request
    def set_visitor_cookie(response):
        token = getattr(g, "new_visitor_token", None)
        if token:
            response.set_cookie(
                VISITOR_COOKIE,
                token,
                max_age=60 * 60 * 24 * 365,
                httponly=True,
                secure=current_app.config["SESSION_COOKIE_SECURE"],
                samesite="Lax",
                path="/",
            )
        return response

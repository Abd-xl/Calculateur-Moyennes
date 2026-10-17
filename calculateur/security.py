"""Authentification admin et cycle de vie des profils anonymes."""
import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from functools import wraps

from flask import g, redirect, request, session, url_for

from .extensions import db


VISITOR_COOKIE = "calculateur_visitor"


def hash_token(token):
    """Hache le jeton du cookie avant de le rechercher en base."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def admin_required(view):
    """Refuse l'accès aux vues d'administration sans session authentifiée."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin.admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def register_browser_hooks(app):
    """Attache à l'application les hooks existants d'identification des visiteurs."""
    from .models import Visitor

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
            visitor.last_seen_at = datetime.now(timezone.utc)
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
                secure=app.config["SESSION_COOKIE_SECURE"],
                samesite="Lax",
                path="/",
            )
        return response

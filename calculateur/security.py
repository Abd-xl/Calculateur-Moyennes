"""Fonctions transversales liées aux requêtes et à l'administration."""

import hashlib
import os
from functools import wraps

from flask import request, session, redirect, url_for
from flask_limiter.util import get_remote_address


VISITOR_COOKIE = "calculateur_visitor"


def get_client_ip():
    """Retourne l'IP cliente selon l'environnement d'exécution."""
    if os.environ.get("RENDER") == "true":
        # Render places the client address first in X-Forwarded-For.
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()
    return get_remote_address()


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped

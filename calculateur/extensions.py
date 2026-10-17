"""Extensions partagées par les modules de l'application."""
import os

from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect


db = SQLAlchemy()
csrf = CSRFProtect()


def get_client_ip():
    """Retourne l'adresse cliente utilisée pour limiter les tentatives de connexion."""
    if os.environ.get("RENDER") == "true":
        # Conserver ici le comportement actuellement utilisé sur Render :
        # la plateforme place l'IP cliente au début de X-Forwarded-For.
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()
    return get_remote_address()


limiter = Limiter(key_func=get_client_ip, default_limits=[])

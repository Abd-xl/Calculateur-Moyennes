"""Instances d'extensions partagées par l'application."""

import os

from flask_limiter import Limiter
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_migrate import Migrate

from calculateur.security import get_client_ip

db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)
migrate = Migrate()

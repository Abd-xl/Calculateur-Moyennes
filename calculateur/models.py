"""Modèles SQLAlchemy de l'application."""
from datetime import datetime, timezone

from .extensions import db


def utcnow():
    """Retourne l'heure UTC avec fuseau, utilisée pour les dates de visite."""
    return datetime.now(timezone.utc)


class Visitor(db.Model):
    """Profil de données associé à un navigateur anonyme."""

    __tablename__ = "anonymous_visitors"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    browser_info = db.Column(db.String(512), nullable=False, default="Inconnu")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    data = db.Column(db.JSON, nullable=False, default=lambda: {"notes": {}, "coef": {}})
    # False avant le premier échange validé : l'ancien localStorage peut alors être importé une fois.
    data_initialized = db.Column(db.Boolean, nullable=False, default=False)

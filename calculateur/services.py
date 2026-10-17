"""Accès aux données du profil visiteur courant."""
import copy

from flask import g

from domaine import _valider_donnees

from .extensions import db


EMPTY_DATA = {"notes": {}, "coef": {}}


def current_data():
    """Renvoie une copie des données courantes pour isoler les mutations de route."""
    return copy.deepcopy(getattr(g.visitor, "data", None) or EMPTY_DATA)


def save_data(data):
    """Valide et persiste l'état complet du visiteur courant."""
    _valider_donnees(data)
    g.visitor.data = copy.deepcopy(data)
    g.visitor.data_initialized = True
    db.session.commit()

"""Adaptateur SQLAlchemy entre un profil visiteur et l'état métier."""

from copy import deepcopy

from calculateur.services.validation import validate_data


EMPTY_GRADEBOOK = {"notes": {}, "coef": {}}


def load_gradebook(visitor):
    return deepcopy(visitor.data or EMPTY_GRADEBOOK)


def save_gradebook(visitor, data, session):
    validate_data(data)
    visitor.data = deepcopy(data)
    visitor.data_initialized = True
    session.commit()

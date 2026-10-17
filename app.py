"""Point d'entrée WSGI rétrocompatible.

Le code applicatif est organisé dans le package `calculateur`. Les exports `app`,
`db` et `Visitor` sont conservés pour Gunicorn, les tests historiques et les outils.
"""
import os

from calculateur import create_app
from calculateur.extensions import db
from calculateur.models import Visitor


app = create_app()

__all__ = ["app", "create_app", "db", "Visitor"]


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "true").lower() == "true")

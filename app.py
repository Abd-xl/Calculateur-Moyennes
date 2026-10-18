"""Point d'entrée historique conservé pour Gunicorn et les tests."""

import os

from calculateur import create_app
from calculateur.extensions import db
from calculateur.models import Visitor

app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")

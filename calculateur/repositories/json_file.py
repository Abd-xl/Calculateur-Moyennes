"""Persistance atomique du format JSON historique utilisé par le CLI."""

import json
import os
import tempfile
from pathlib import Path

from calculateur.services.validation import DonneesInvalidesError, validate_data


class SauvegardeError(RuntimeError):
    """Levée lorsqu'une écriture du fichier de notes échoue."""


class JsonGradebookRepository:
    def __init__(self, path="notes.json"):
        self.path = Path(path)

    def load(self):
        try:
            with self.path.open("r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError as error:
                    raise DonneesInvalidesError(
                        f"Le fichier {self.path.name} contient un JSON invalide : {error.msg}."
                    ) from error
            validate_data(data)
            return data
        except FileNotFoundError:
            return None

    def save(self, data):
        validate_data(data)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(data, temporary_file)

            os.replace(temporary_path, self.path)
        except (OSError, TypeError) as error:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except OSError:
                    pass
            raise SauvegardeError(
                f"Impossible de sauvegarder les données : {error}"
            ) from error

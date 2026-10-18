import os

from calculateur.services.validation import DonneesInvalidesError, validate_data
from calculateur.repositories.json_file import JsonGradebookRepository, SauvegardeError

notes = {}
coef = {}
_repository = JsonGradebookRepository()


def _valider_donnees(data):
    validate_data(data)


def remplacer_donnees(data):
    _valider_donnees(data)

    notes.clear()
    coef.clear()
    notes.update(data["notes"])
    coef.update(data["coef"])


def sauvegarder():
    _repository.save({"notes": notes, "coef": coef})
    print("Données sauvegardées avec succès.")


def charger():
    data = _repository.load()
    if data is None:
        notes.clear()
        coef.clear()
        return

    remplacer_donnees(data)
    print("Données chargées avec succès.")


def reinitialiser():
    confirmation = input("\nVoulez-vous réinitialiser ? y/n: ")
    if confirmation.lower() == "y":
        anciennes_notes = notes.copy()
        anciens_coef = coef.copy()

        notes.clear()
        coef.clear()

        try:
            sauvegarder()
        except SauvegardeError:
            notes.clear()
            coef.clear()
            notes.update(anciennes_notes)
            coef.update(anciens_coef)
            raise

        print("Success")
    elif confirmation.lower() == "n":
        print("Annulé.")

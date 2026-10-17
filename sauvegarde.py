import json
import os
import tempfile

from domaine import DonneesInvalidesError, _valider_donnees

notes = {}
coef = {}


class SauvegardeError(RuntimeError):
    """Levée lorsqu'une sauvegarde des données échoue."""


def remplacer_donnees(data):
    _valider_donnees(data)

    notes.clear()
    coef.clear()
    notes.update(data["notes"])
    coef.update(data["coef"])


def sauvegarder():
    chemin_temporaire = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=".",
            delete=False,
        ) as fichier_temporaire:
            chemin_temporaire = fichier_temporaire.name
            json.dump(
                {"notes": notes, "coef": coef},
                fichier_temporaire,
            )

        os.replace(chemin_temporaire, "notes.json")
        print("Données sauvegardées avec succès.")

    except (OSError, TypeError) as erreur:
        if chemin_temporaire is not None:
            try:
                os.remove(chemin_temporaire)
            except OSError:
                pass

        raise SauvegardeError(
            f"Impossible de sauvegarder les données : {erreur}"
        ) from erreur


def charger():
    try:
        with open("notes.json", "r", encoding="utf-8") as fichier:
            try:
                data = json.load(fichier)
            except json.JSONDecodeError as erreur:
                raise DonneesInvalidesError(
                    f"Le fichier notes.json contient un JSON invalide : {erreur.msg}."
                ) from erreur

            _valider_donnees(data)

    except FileNotFoundError:
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

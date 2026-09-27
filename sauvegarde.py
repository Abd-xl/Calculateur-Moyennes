import json
import os
import tempfile

notes = {}
coef = {}


def _valider_donnees(data):
    if not isinstance(data, dict):
        raise ValueError("Les données doivent être un dictionnaire.")

    notes_data = data.get("notes")
    coef_data = data.get("coef")

    if not isinstance(notes_data, dict):
        raise ValueError("Les notes doivent être un dictionnaire.")

    if not isinstance(coef_data, dict):
        raise ValueError("Les coefficients doivent être un dictionnaire.")

    if set(notes_data) != set(coef_data):
        raise ValueError(
            "Les matières et les coefficients ne correspondent pas."
        )


def sauvegarder():
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=".",
            delete=False,
        ) as fichier_temporaire:
            json.dump(
                {"notes": notes, "coef": coef},
                fichier_temporaire,
            )
            chemin_temporaire = fichier_temporaire.name

        os.replace(chemin_temporaire, "notes.json")
        print("Données sauvegardées avec succès.")

    except (OSError, TypeError) as e:
        print(f"Erreur lors de la sauvegarde des données : {e}")


def charger():
    global notes, coef
    try:
        with open("notes.json", "r") as f:
            data = json.load(f)
            notes.update(data.get("notes", {}))
            coef.update(data.get("coef", {}))
            print("Données chargées avec succès.")
    except FileNotFoundError:
        notes.clear()
        coef.clear()
    except (json.JSONDecodeError, TypeError):
        notes.clear()
        coef.clear()


def reinitialiser():
    global notes, coef
    comfirmation = input("
Voulez vous reinitialiser ? y/n: ")
    if comfirmation.lower() == "y":
        notes.clear()
        coef.clear()
        sauvegarder()
        print("Success")
    elif comfirmation.lower() == "n":
        print("Annulé.")

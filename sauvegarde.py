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

    for matiere, liste_notes in notes_data.items():
        if not isinstance(matiere, str) or not matiere.strip():
            raise ValueError("Le nom de la matière est invalide.")

        if not isinstance(liste_notes, list):
            raise ValueError(
                f"Les notes de {matiere} doivent être une liste."
            )

        coefficient = coef_data[matiere]
        if (
            isinstance(coefficient, bool)
            or not isinstance(coefficient, int)
            or coefficient <= 0
        ):
            raise ValueError(
                f"Le coefficient de {matiere} doit être un entier positif."
            )

        for note_data in liste_notes:
            if not isinstance(note_data, dict):
                raise ValueError(
                    f"Une note de {matiere} doit être un dictionnaire."
                )

            if set(note_data) != {"note", "bareme"}:
                raise ValueError(
                    f"Une note de {matiere} doit contenir note et bareme."
                )

            note = note_data["note"]
            bareme = note_data["bareme"]

            if (
                isinstance(note, bool)
                or not isinstance(note, (int, float))
            ):
                raise ValueError("La note doit être un nombre.")

            if bareme not in (10, 20):
                raise ValueError("Le barème doit être 10 ou 20.")

            if not 0 <= note <= bareme:
                raise ValueError(
                    f"La note doit être comprise entre 0 et {bareme}."
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

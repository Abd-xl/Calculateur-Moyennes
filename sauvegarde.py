import json
import os
import tempfile

notes = {}
coef = {}


class DonneesInvalidesError(ValueError):
    """Levée lorsque notes.json existe mais ne peut pas être utilisé."""


def _valider_donnees(data):
    if not isinstance(data, dict):
        raise DonneesInvalidesError("Les données doivent être un dictionnaire.")

    notes_data = data.get("notes")
    coef_data = data.get("coef")

    if not isinstance(notes_data, dict):
        raise DonneesInvalidesError("Les notes doivent être un dictionnaire.")

    if not isinstance(coef_data, dict):
        raise DonneesInvalidesError("Les coefficients doivent être un dictionnaire.")

    if set(notes_data) != set(coef_data):
        raise DonneesInvalidesError(
            "Les matières et les coefficients ne correspondent pas."
        )

    for matiere, liste_notes in notes_data.items():
        if not isinstance(matiere, str) or not matiere.strip():
            raise DonneesInvalidesError("Le nom de la matière est invalide.")

        if not isinstance(liste_notes, list):
            raise DonneesInvalidesError(
                f"Les notes de {matiere} doivent être une liste."
            )

        coefficient = coef_data[matiere]
        if (
            isinstance(coefficient, bool)
            or not isinstance(coefficient, int)
            or coefficient <= 0
        ):
            raise DonneesInvalidesError(
                f"Le coefficient de {matiere} doit être un entier positif."
            )

        for note_data in liste_notes:
            if not isinstance(note_data, dict):
                raise DonneesInvalidesError(
                    f"Une note de {matiere} doit être un dictionnaire."
                )

            if set(note_data) != {"note", "bareme"}:
                raise DonneesInvalidesError(
                    f"Une note de {matiere} doit contenir note et bareme."
                )

            note = note_data["note"]
            bareme = note_data["bareme"]

            if isinstance(note, bool) or not isinstance(note, (int, float)):
                raise DonneesInvalidesError("La note doit être un nombre.")

            if bareme not in (10, 20):
                raise DonneesInvalidesError("Le barème doit être 10 ou 20.")

            if not 0 <= note <= bareme:
                raise DonneesInvalidesError(
                    f"La note doit être comprise entre 0 et {bareme}."
                )


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
        print(f"Erreur lors de la sauvegarde des données : {erreur}")
        if chemin_temporaire is not None:
            try:
                os.remove(chemin_temporaire)
            except OSError:
                pass


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

    notes.clear()
    coef.clear()
    notes.update(data["notes"])
    coef.update(data["coef"])
    print("Données chargées avec succès.")


def reinitialiser():
    confirmation = input("\nVoulez-vous réinitialiser ? y/n: ")
    if confirmation.lower() == "y":
        notes.clear()
        coef.clear()
        sauvegarder()
        print("Success")
    elif confirmation.lower() == "n":
        print("Annulé.")

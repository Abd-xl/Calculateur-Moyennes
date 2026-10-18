"""Validation du format stable de données du carnet de notes."""


class DonneesInvalidesError(ValueError):
    """Levée lorsque l'état des notes ne respecte pas le format attendu."""


def validate_data(data):
    if not isinstance(data, dict):
        raise DonneesInvalidesError("Les données doivent être un dictionnaire.")

    notes_data = data.get("notes")
    coef_data = data.get("coef")

    if not isinstance(notes_data, dict):
        raise DonneesInvalidesError("Les notes doivent être un dictionnaire.")
    if not isinstance(coef_data, dict):
        raise DonneesInvalidesError("Les coefficients doivent être un dictionnaire.")
    if set(notes_data) != set(coef_data):
        raise DonneesInvalidesError("Les matières et les coefficients ne correspondent pas.")

    for subject, subject_notes in notes_data.items():
        if not isinstance(subject, str) or not subject.strip():
            raise DonneesInvalidesError("Le nom de la matière est invalide.")
        if not isinstance(subject_notes, list):
            raise DonneesInvalidesError(f"Les notes de {subject} doivent être une liste.")

        coefficient = coef_data[subject]
        if isinstance(coefficient, bool) or not isinstance(coefficient, int) or coefficient <= 0:
            raise DonneesInvalidesError(
                f"Le coefficient de {subject} doit être un entier positif."
            )

        for note_data in subject_notes:
            if not isinstance(note_data, dict):
                raise DonneesInvalidesError(f"Une note de {subject} doit être un dictionnaire.")
            if set(note_data) != {"note", "bareme"}:
                raise DonneesInvalidesError(f"Une note de {subject} doit contenir note et bareme.")

            grade, scale = note_data["note"], note_data["bareme"]
            if isinstance(grade, bool) or not isinstance(grade, (int, float)):
                raise DonneesInvalidesError("La note doit être un nombre.")
            if isinstance(scale, bool) or scale not in (10, 20):
                raise DonneesInvalidesError("Le barème doit être 10 ou 20.")
            if not 0 <= grade <= scale:
                raise DonneesInvalidesError(
                    f"La note doit être comprise entre 0 et {scale}."
                )

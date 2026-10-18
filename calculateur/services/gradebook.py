"""Règles métier sans dépendance à Flask, SQLAlchemy ou au stockage."""


def find_subject(notes, subject):
    name = subject.strip()
    if not name:
        return None
    if name in notes:
        return name
    return next(
        (existing for existing in notes if existing.strip().casefold() == name.casefold()),
        None,
    )


def add_note(data, subject, grade, coefficient, scale=20):
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("La matière ne peut pas être vide.")
    if isinstance(grade, bool) or not isinstance(grade, (int, float)):
        raise TypeError("La note doit être un nombre.")
    if isinstance(scale, bool) or scale not in (10, 20):
        raise ValueError("Le barème doit être 10 ou 20.")
    if not 0 <= grade <= scale:
        raise ValueError(f"La note doit être comprise entre 0 et {scale}.")
    if isinstance(coefficient, bool) or not isinstance(coefficient, int):
        raise TypeError("Le coefficient doit être un entier.")
    if coefficient <= 0:
        raise ValueError("Le coefficient doit être supérieur à 0.")

    notes, coefficients = data["notes"], data["coef"]
    existing = find_subject(notes, subject)
    if existing is not None:
        if coefficients[existing] != coefficient:
            raise ValueError(
                f"La matière existe déjà avec le coefficient {coefficients[existing]}."
            )
        subject = existing
    else:
        subject = subject.strip()
        notes[subject] = []
        coefficients[subject] = coefficient

    notes[subject].append({"note": grade, "bareme": scale})
    return subject


def modify_note(data, subject, index, grade):
    subject = find_subject(data["notes"], subject)
    if subject is None:
        raise ValueError("Cette matière n'existe pas.")
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(data["notes"][subject]):
        raise ValueError("Cette note n'existe pas dans cette matière.")

    note = data["notes"][subject][index]
    if isinstance(grade, bool) or not isinstance(grade, (int, float)):
        raise TypeError("La note doit être un nombre.")
    if not 0 <= grade <= note["bareme"]:
        raise ValueError(
            f"La nouvelle note doit être comprise entre 0 et {note['bareme']}."
        )
    note["note"] = grade


def delete_note(data, subject, index):
    subject = find_subject(data["notes"], subject)
    if subject is None:
        raise ValueError("Cette matière n'existe pas.")
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(data["notes"][subject]):
        raise ValueError("Cette note n'existe pas dans cette matière.")
    del data["notes"][subject][index]


def delete_subject(data, subject):
    subject = find_subject(data["notes"], subject)
    if subject is None:
        raise ValueError("Cette matière n'existe pas.")
    del data["notes"][subject]
    del data["coef"][subject]

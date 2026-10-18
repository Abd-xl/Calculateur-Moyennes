"""Calcul des moyennes à partir du format de données historique."""


def calculate_subject_average(subject_notes):
    if not subject_notes:
        return 0
    return sum(note["note"] * 20 / note["bareme"] for note in subject_notes) / len(subject_notes)


def calculate_averages(data):
    """Retourne les moyennes par matière et la moyenne générale pondérée."""
    notes = data["notes"]
    coefficients = data["coef"]
    averages = {}
    weighted_total = coefficient_total = 0

    for subject, subject_notes in notes.items():
        average = calculate_subject_average(subject_notes)
        averages[subject] = average
        weighted_total += average * coefficients[subject]
        coefficient_total += coefficients[subject]

    overall = weighted_total / coefficient_total if coefficient_total else 0
    return averages, overall

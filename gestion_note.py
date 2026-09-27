from sauvegarde import SauvegardeError, sauvegarder
from sauvegarde import notes, coef


def convertir_sur_20(note):
    return note["note"] * 20 / note["bareme"]


def calculer_moyenne(liste_notes):
    if len(liste_notes) == 0:
        return 0
    return sum(convertir_sur_20(note) for note in liste_notes) / len(liste_notes)


def _trouver_matiere(matiere):
    nom = matiere.strip()
    if not nom:
        return None
    if nom in notes:
        return nom
    for nom_existant in notes:
        if nom_existant.strip().casefold() == nom.casefold():
            return nom_existant
    return None


def ajouter_note(matiere, note, coefficient, bareme=20):
    if not matiere.strip():
        raise ValueError("La matière ne peut pas être vide.")
    if not isinstance(note, (int, float)):
        raise TypeError("La note doit être un nombre.")
    if bareme not in (10, 20):
        raise ValueError("Le barème doit être 10 ou 20.")
    if not 0 <= note <= bareme:
        raise ValueError(f"La note doit être comprise entre 0 et {bareme}.")
    if not isinstance(coefficient, int):
        raise TypeError("Le coefficient doit être un entier.")
    if coefficient <= 0:
        raise ValueError("Le coefficient doit être supérieur à 0.")

    matiere_existante = _trouver_matiere(matiere)
    nouvelle_matiere = matiere_existante is None

    if matiere_existante is not None:
        if coef[matiere_existante] != coefficient:
            raise ValueError(
                f"La matière existe déjà avec le coefficient {coef[matiere_existante]}."
            )
        matiere = matiere_existante
    else:
        matiere = matiere.strip()
        notes[matiere] = []
        coef[matiere] = coefficient

    notes[matiere].append({"note": note, "bareme": bareme})

    try:
        sauvegarder()
    except SauvegardeError:
        notes[matiere].pop()

        if nouvelle_matiere:
            del notes[matiere]
            del coef[matiere]

        raise


def modifier_note(matiere, index, nouvelle_note):
    matiere = _trouver_matiere(matiere)
    if matiere is None:
        raise ValueError("Cette matière n'existe pas.")
    if not isinstance(index, int) or not 0 <= index < len(notes[matiere]):
        raise ValueError("Cette note n'existe pas dans cette matière.")

    bareme = notes[matiere][index]["bareme"]
    if not 0 <= nouvelle_note <= bareme:
        raise ValueError(
            f"La nouvelle note doit être comprise entre 0 et {bareme}."
        )

    ancienne_note = notes[matiere][index]["note"]
    notes[matiere][index]["note"] = nouvelle_note

    try:
        sauvegarder()
    except SauvegardeError:
        notes[matiere][index]["note"] = ancienne_note
        raise


def supprimer_matiere(matiere):
    matiere = _trouver_matiere(matiere)
    if matiere is None:
        raise ValueError("Cette matière n'existe pas.")

    anciennes_notes = notes[matiere].copy()
    ancien_coef = coef[matiere]

    del notes[matiere]
    del coef[matiere]

    try:
        sauvegarder()
    except SauvegardeError:
        notes[matiere] = anciennes_notes
        coef[matiere] = ancien_coef
        raise


def supprimer_note(matiere, index):
    matiere = _trouver_matiere(matiere)
    if matiere is None:
        raise ValueError("Cette matière n'existe pas.")
    if not isinstance(index, int) or not 0 <= index < len(notes[matiere]):
        raise ValueError("Cette note n'existe pas dans cette matière.")

    note_supprimee = notes[matiere].pop(index)

    try:
        sauvegarder()
    except SauvegardeError:
        notes[matiere].insert(index, note_supprimee)
        raise


def calculer_moyennes():
    resultats = {}
    somme_ponderee = 0
    somme_coef = 0

    for matiere, liste_notes in notes.items():
        moyenne = calculer_moyenne(liste_notes)
        resultats[matiere] = moyenne
        somme_ponderee += moyenne * coef[matiere]
        somme_coef += coef[matiere]

    moyenne_generale = somme_ponderee / somme_coef if somme_coef > 0 else 0
    return resultats, moyenne_generale

"""Règles métier pures partagées par l'application web et l'ancienne CLI.

Ce module n'importe ni Flask ni le système de stockage : les mêmes validations,
calculs et opérations s'appliquent quel que soit le point d'entrée.
"""
import math


class DonneesInvalidesError(ValueError):
    """Levée lorsque la structure ou le contenu des notes est invalide."""


def _valider_donnees(data):
    """Valide le contrat JSON commun aux deux versions de l'application."""
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

    for matiere, liste_notes in notes_data.items():
        if not isinstance(matiere, str) or not matiere.strip():
            raise DonneesInvalidesError("Le nom de la matière est invalide.")
        if not isinstance(liste_notes, list):
            raise DonneesInvalidesError(f"Les notes de {matiere} doivent être une liste.")

        coefficient = coef_data[matiere]
        if isinstance(coefficient, bool) or not isinstance(coefficient, int) or coefficient <= 0:
            raise DonneesInvalidesError(f"Le coefficient de {matiere} doit être un entier positif.")

        for note_data in liste_notes:
            if not isinstance(note_data, dict):
                raise DonneesInvalidesError(f"Une note de {matiere} doit être un dictionnaire.")
            if set(note_data) != {"note", "bareme"}:
                raise DonneesInvalidesError(f"Une note de {matiere} doit contenir note et bareme.")

            note = note_data["note"]
            bareme = note_data["bareme"]
            if isinstance(note, bool) or not isinstance(note, (int, float)):
                raise DonneesInvalidesError("La note doit être un nombre.")
            if not math.isfinite(note):
                raise DonneesInvalidesError("La note doit être un nombre fini.")
            if isinstance(bareme, bool) or bareme not in (10, 20):
                raise DonneesInvalidesError("Le barème doit être 10 ou 20.")
            if not 0 <= note <= bareme:
                raise DonneesInvalidesError(f"La note doit être comprise entre 0 et {bareme}.")


def trouver_matiere(notes, matiere):
    """Trouve une matière sans tenir compte des espaces extérieurs ni de la casse."""
    if not isinstance(matiere, str) or not matiere.strip():
        return None
    nom = matiere.strip()
    if nom in notes:
        return nom
    return next(
        (existing for existing in notes if existing.strip().casefold() == nom.casefold()),
        None,
    )


def convertir_sur_20(note):
    """Convertit une note conservant son barème d'origine sur /20."""
    return note["note"] * 20 / note["bareme"]


def calculer_moyenne(liste_notes):
    """Calcule la moyenne arithmétique d'une matière; zéro si elle est vide."""
    if not liste_notes:
        return 0
    return sum(convertir_sur_20(note) for note in liste_notes) / len(liste_notes)


def calculer_moyennes(notes, coefficients):
    """Renvoie les moyennes par matière et la moyenne générale pondérée.

    Une matière sans note reste visible avec une moyenne de 0, mais elle ne
    contribue pas à la moyenne générale : aucune évaluation n'est pas une note nulle.
    """
    moyennes = {
        matiere: calculer_moyenne(liste_notes)
        for matiere, liste_notes in notes.items()
    }
    matieres_evaluees = [
        matiere for matiere, liste_notes in notes.items() if liste_notes
    ]
    total_coefficients = sum(coefficients[matiere] for matiere in matieres_evaluees)
    if not total_coefficients:
        return moyennes, 0
    total_pondere = sum(
        moyennes[matiere] * coefficients[matiere]
        for matiere in matieres_evaluees
    )
    return moyennes, total_pondere / total_coefficients


def _valider_nouvelle_note(note, bareme):
    if isinstance(note, bool) or not isinstance(note, (int, float)) or not math.isfinite(note):
        raise ValueError("La note doit être un nombre fini.")
    if isinstance(bareme, bool) or not isinstance(bareme, int) or bareme not in (10, 20):
        raise ValueError("Le barème doit être 10 ou 20.")
    if not 0 <= note <= bareme:
        raise ValueError(f"La note doit être comprise entre 0 et {bareme}.")


def _valider_coefficient(coefficient):
    if isinstance(coefficient, bool) or not isinstance(coefficient, int):
        raise TypeError("Le coefficient doit être un entier.")
    if coefficient <= 0:
        raise ValueError("Le coefficient doit être supérieur à 0.")


def ajouter_note_donnees(data, matiere, note, coefficient, bareme=20):
    """Ajoute une note à une matière, en modifiant le dictionnaire fourni."""
    if not isinstance(data, dict) or not isinstance(data.get("notes"), dict) or not isinstance(data.get("coef"), dict):
        raise DonneesInvalidesError("Les données doivent contenir les dictionnaires notes et coef.")
    if not isinstance(matiere, str) or not matiere.strip():
        raise ValueError("La matière ne peut pas être vide.")
    _valider_nouvelle_note(note, bareme)
    _valider_coefficient(coefficient)

    existing = trouver_matiere(data["notes"], matiere)
    created = existing is None
    if existing is not None:
        if data["coef"][existing] != coefficient:
            raise ValueError(f"La matière existe déjà avec le coefficient {data['coef'][existing]}.")
        matiere = existing
    else:
        matiere = matiere.strip()
        data["notes"][matiere] = []
        data["coef"][matiere] = coefficient

    data["notes"][matiere].append({"note": note, "bareme": bareme})
    return matiere, created


def modifier_note_donnees(data, matiere, index, nouvelle_note):
    """Modifie une note en refusant les index négatifs ou hors limites."""
    matiere = trouver_matiere(data["notes"], matiere)
    if matiere is None:
        raise ValueError("Cette matière n'existe pas.")
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(data["notes"][matiere]):
        raise ValueError("Cette note n'existe pas dans cette matière.")
    bareme = data["notes"][matiere][index]["bareme"]
    _valider_nouvelle_note(nouvelle_note, bareme)
    ancienne_note = data["notes"][matiere][index]["note"]
    data["notes"][matiere][index]["note"] = nouvelle_note
    return matiere, ancienne_note


def supprimer_note_donnees(data, matiere, index):
    """Supprime une note et renvoie la note retirée pour un éventuel rollback."""
    matiere = trouver_matiere(data["notes"], matiere)
    if matiere is None:
        raise ValueError("Cette matière n'existe pas.")
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(data["notes"][matiere]):
        raise ValueError("Cette note n'existe pas dans cette matière.")
    note_supprimee = data["notes"][matiere].pop(index)
    return matiere, note_supprimee


def supprimer_matiere_donnees(data, matiere):
    """Supprime une matière et ses coefficients; renvoie la clé canonique."""
    matiere = trouver_matiere(data["notes"], matiere)
    if matiere is None:
        raise ValueError("Cette matière n'existe pas.")
    del data["notes"][matiere]
    del data["coef"][matiere]
    return matiere

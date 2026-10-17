"""Opérations du programme CLI avec sauvegarde JSON historique.

Les règles métier pures sont partagées avec la version web via `domaine.py`.
Ce module conserve le contrat de fonctions et les dictionnaires attendus par cli.py.
"""
from domaine import (
    ajouter_note_donnees,
    calculer_moyenne,
    convertir_sur_20 as _convertir_sur_20,
    calculer_moyennes as _calculer_moyennes_donnees,
    modifier_note_donnees,
    supprimer_matiere_donnees,
    supprimer_note_donnees,
    trouver_matiere,
)
from sauvegarde import SauvegardeError, sauvegarder
from sauvegarde import notes, coef


def convertir_sur_20(note):
    return _convertir_sur_20(note)


def _trouver_matiere(matiere):
    return trouver_matiere(notes, matiere)


def _donnees():
    # Les dictionnaires sont partagés avec sauvegarde.py afin de conserver la CLI.
    return {"notes": notes, "coef": coef}


def ajouter_note(matiere, note, coefficient, bareme=20):
    nom, nouvelle_matiere = ajouter_note_donnees(
        _donnees(), matiere, note, coefficient, bareme
    )
    try:
        sauvegarder()
    except SauvegardeError:
        notes[nom].pop()
        if nouvelle_matiere:
            del notes[nom]
            del coef[nom]
        raise


def modifier_note(matiere, index, nouvelle_note):
    nom, ancienne_note = modifier_note_donnees(
        _donnees(), matiere, index, nouvelle_note
    )
    try:
        sauvegarder()
    except SauvegardeError:
        notes[nom][index]["note"] = ancienne_note
        raise


def supprimer_matiere(matiere):
    nom = _trouver_matiere(matiere)
    if nom is None:
        raise ValueError("Cette matière n'existe pas.")

    anciennes_notes = notes[nom].copy()
    ancien_coef = coef[nom]
    supprimer_matiere_donnees(_donnees(), nom)
    try:
        sauvegarder()
    except SauvegardeError:
        notes[nom] = anciennes_notes
        coef[nom] = ancien_coef
        raise


def supprimer_note(matiere, index):
    nom, note_supprimee = supprimer_note_donnees(_donnees(), matiere, index)
    try:
        sauvegarder()
    except SauvegardeError:
        notes[nom].insert(index, note_supprimee)
        raise


def calculer_moyennes():
    return _calculer_moyennes_donnees(notes, coef)

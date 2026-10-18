"""Adaptateur historique entre le CLI, le modèle métier et le JSON local."""

from copy import deepcopy

from calculateur.services.gradebook import (
    add_note as add_note_to_data,
    delete_note as delete_note_from_data,
    delete_subject as delete_subject_from_data,
    find_subject,
    modify_note as modify_note_in_data,
)
from calculateur.services.grades import calculate_averages, calculate_subject_average
from sauvegarde import SauvegardeError, coef, notes, sauvegarder


def convertir_sur_20(note):
    return note["note"] * 20 / note["bareme"]


def calculer_moyenne(liste_notes):
    return calculate_subject_average(liste_notes)


def _trouver_matiere(matiere):
    return find_subject(notes, matiere)


def _snapshot():
    return deepcopy(notes), deepcopy(coef)


def _persist_or_restore(snapshot):
    try:
        sauvegarder()
    except SauvegardeError:
        old_notes, old_coef = snapshot
        notes.clear()
        notes.update(old_notes)
        coef.clear()
        coef.update(old_coef)
        raise


def _data():
    return {"notes": notes, "coef": coef}


def ajouter_note(matiere, note, coefficient, bareme=20):
    snapshot = _snapshot()
    add_note_to_data(_data(), matiere, note, coefficient, bareme)
    _persist_or_restore(snapshot)


def modifier_note(matiere, index, nouvelle_note):
    snapshot = _snapshot()
    modify_note_in_data(_data(), matiere, index, nouvelle_note)
    _persist_or_restore(snapshot)


def supprimer_matiere(matiere):
    snapshot = _snapshot()
    delete_subject_from_data(_data(), matiere)
    _persist_or_restore(snapshot)


def supprimer_note(matiere, index):
    snapshot = _snapshot()
    delete_note_from_data(_data(), matiere, index)
    _persist_or_restore(snapshot)


def calculer_moyennes():
    return calculate_averages(_data())

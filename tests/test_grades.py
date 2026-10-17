"""Tests unitaires des calculs et des règles de moyenne."""
import pytest

from domaine import (
    DonneesInvalidesError,
    _valider_donnees,
    ajouter_note_donnees,
    calculer_moyenne,
    calculer_moyennes,
    convertir_sur_20,
    modifier_note_donnees,
    supprimer_note_donnees,
)


def test_convertir_note_sur_bareme_dix():
    assert convertir_sur_20({"note": 10, "bareme": 10}) == 20


def test_moyenne_melangeant_les_baremes():
    assert calculer_moyenne([
        {"note": 10, "bareme": 10},
        {"note": 5, "bareme": 20},
    ]) == 12.5


def test_moyenne_vide_vaut_zero():
    assert calculer_moyenne([]) == 0


def test_moyennes_par_matiere():
    notes = {
        "Maths": [{"note": 15, "bareme": 20}],
        "Physique": [{"note": 8, "bareme": 10}],
    }
    moyennes, generale = calculer_moyennes(notes, {"Maths": 4, "Physique": 2})
    assert moyennes == {"Maths": 15, "Physique": 16}
    assert generale == pytest.approx(15.3333333333)


def test_matiere_sans_note_ne_fait_pas_baisser_la_moyenne_generale():
    notes = {
        "Maths": [{"note": 18, "bareme": 20}],
        "Physique": [],
    }
    moyennes, generale = calculer_moyennes(notes, {"Maths": 4, "Physique": 3})
    assert moyennes == {"Maths": 18, "Physique": 0}
    assert generale == 18


def test_moyenne_generale_est_zero_sans_note():
    assert calculer_moyennes({"Maths": []}, {"Maths": 4}) == ({"Maths": 0}, 0)


def test_actions_metier_refusent_les_index_negatifs():
    data = {
        "notes": {"Maths": [{"note": 10, "bareme": 20}]},
        "coef": {"Maths": 4},
    }

    with pytest.raises(ValueError):
        modifier_note_donnees(data, "Maths", -1, 12)
    with pytest.raises(ValueError):
        supprimer_note_donnees(data, "Maths", -1)
    assert data["notes"]["Maths"] == [{"note": 10, "bareme": 20}]


@pytest.mark.parametrize("note", [True, float("nan"), float("inf"), -float("inf")])
def test_validation_refuse_les_notes_booleennes_ou_non_finies(note):
    data = {"notes": {"Maths": [{"note": note, "bareme": 20}]}, "coef": {"Maths": 4}}
    with pytest.raises(DonneesInvalidesError):
        _valider_donnees(data)


def test_ajout_et_suppression_partagent_les_regles_metier():
    data = {"notes": {}, "coef": {}}
    subject, created = ajouter_note_donnees(data, "  maths ", 14, 3, 20)
    assert subject == "maths"
    assert created is True
    assert data == {"notes": {"maths": [{"note": 14, "bareme": 20}]}, "coef": {"maths": 3}}
    subject, removed = supprimer_note_donnees(data, "MATHS", 0)
    assert subject == "maths"
    assert removed == {"note": 14, "bareme": 20}
    assert data == {"notes": {"maths": []}, "coef": {"maths": 3}}

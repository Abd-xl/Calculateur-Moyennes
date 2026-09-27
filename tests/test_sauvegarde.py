import pytest

from sauvegarde import _valider_donnees


def test_valider_donnees_accepte_une_structure_valide():
    data = {
        "notes": {"Maths": []},
        "coef": {"Maths": 4},
    }

    _valider_donnees(data)


@pytest.mark.parametrize("data", [None, [], "bonjour", 42])
def test_valider_donnees_refuse_un_conteneur_invalide(data):
    with pytest.raises(ValueError):
        _valider_donnees(data)


def test_valider_donnees_refuse_des_notes_non_dict():
    with pytest.raises(ValueError):
        _valider_donnees({
            "notes": [],
            "coef": {},
        })


def test_valider_donnees_refuse_des_coefficients_non_dict():
    with pytest.raises(ValueError):
        _valider_donnees({
            "notes": {},
            "coef": [],
        })


def test_valider_donnees_refuse_des_matieres_incoherentes():
    with pytest.raises(ValueError):
        _valider_donnees({
            "notes": {"Maths": []},
            "coef": {"Physique": 3},
        })


def test_valider_donnees_refuse_une_liste_de_notes_invalide():
    with pytest.raises(ValueError):
        _valider_donnees({
            "notes": {"Maths": "bonjour"},
            "coef": {"Maths": 4},
        })


def test_valider_donnees_refuse_un_coefficient_invalide():
    with pytest.raises(ValueError):
        _valider_donnees({
            "notes": {"Maths": []},
            "coef": {"Maths": 0},
        })


def test_valider_donnees_refuse_une_note_mal_structuree():
    with pytest.raises(ValueError):
        _valider_donnees({
            "notes": {"Maths": [{"note": 15}]},
            "coef": {"Maths": 4},
        })


@pytest.mark.parametrize(
    "note_data",
    [
        {"note": "15", "bareme": 20},
        {"note": 21, "bareme": 20},
        {"note": 8, "bareme": 15},
    ],
)
def test_valider_donnees_refuse_une_note_invalide(note_data):
    with pytest.raises(ValueError):
        _valider_donnees({
            "notes": {"Maths": [note_data]},
            "coef": {"Maths": 4},
        })

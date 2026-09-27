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

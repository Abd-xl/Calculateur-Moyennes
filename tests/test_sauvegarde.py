import pytest

from sauvegarde import DonneesInvalidesError, _valider_donnees


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


def test_charger_signale_un_json_structurellement_invalide(monkeypatch, tmp_path):
    fichier = tmp_path / "notes.json"
    fichier.write_text(
        '{"notes": {"Maths": "invalide"}, "coef": {"Maths": 4}}',
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    import sauvegarde

    sauvegarde.notes["Ancienne"] = []
    sauvegarde.coef["Ancienne"] = 2

    with pytest.raises(DonneesInvalidesError):
        sauvegarde.charger()

    assert sauvegarde.notes == {"Ancienne": []}
    assert sauvegarde.coef == {"Ancienne": 2}


def test_charger_signale_un_json_invalide(monkeypatch, tmp_path):
    fichier = tmp_path / "notes.json"
    fichier.write_text(
        '{"notes": ',
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    import sauvegarde

    with pytest.raises(DonneesInvalidesError, match="JSON invalide"):
        sauvegarde.charger()


def test_charger_accepte_un_json_valide(monkeypatch, tmp_path):
    fichier = tmp_path / "notes.json"
    fichier.write_text(
        '{"notes": {"Maths": [{"note": 15, "bareme": 20}]}, '
        '"coef": {"Maths": 4}}',
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    import sauvegarde

    sauvegarde.notes.clear()
    sauvegarde.coef.clear()

    sauvegarde.charger()

    assert sauvegarde.notes == {
        "Maths": [{"note": 15, "bareme": 20}]
    }
    assert sauvegarde.coef == {"Maths": 4}


def test_sauvegarder_signale_une_erreur_systeme(monkeypatch, tmp_path):
    import sauvegarde

    monkeypatch.chdir(tmp_path)
    sauvegarde.notes.clear()
    sauvegarde.coef.clear()
    sauvegarde.notes["Maths"] = [{"note": 15, "bareme": 20}]
    sauvegarde.coef["Maths"] = 4

    def remplacement_en_echec(source, destination):
        raise OSError("disque indisponible")

    monkeypatch.setattr(sauvegarde.os, "replace", remplacement_en_echec)

    with pytest.raises(sauvegarde.SauvegardeError, match="disque indisponible"):
        sauvegarde.sauvegarder()

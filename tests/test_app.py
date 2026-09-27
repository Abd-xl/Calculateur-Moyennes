import pytest

import app
import gestion_note
import sauvegarde


@pytest.fixture(autouse=True)
def etat_propre(monkeypatch):
    notes_test = {}
    coef_test = {}

    monkeypatch.setattr(sauvegarde, "notes", notes_test)
    monkeypatch.setattr(sauvegarde, "coef", coef_test)
    monkeypatch.setattr(gestion_note, "notes", notes_test)
    monkeypatch.setattr(gestion_note, "coef", coef_test)
    monkeypatch.setattr(app, "notes", notes_test)
    monkeypatch.setattr(app, "coef", coef_test)
    monkeypatch.setattr(gestion_note, "sauvegarder", lambda: None)

    app.app.config.update(TESTING=True)


def test_supprimer_refuse_un_index_invalide():
    gestion_note.ajouter_note("Maths", 15, 4)

    client = app.app.test_client()

    response = client.post(
        "/supprimer",
        data={"matiere": "Maths", "index": "1"},
    )

    assert response.status_code == 200
    assert b"Cette note n'existe pas dans cette matiÃ¨re." in response.data


def test_modifier_refuse_un_champ_manquant():
    gestion_note.ajouter_note("Maths", 15, 4)

    client = app.app.test_client()

    response = client.post(
        "/modifier",
        data={"matiere": "Maths", "index": "0"},
    )

    assert response.status_code == 200


def test_modifier_refuse_une_note_non_numerique():
    gestion_note.ajouter_note("Maths", 15, 4)

    client = app.app.test_client()

    response = client.post(
        "/modifier",
        data={
            "matiere": "Maths",
            "index": "0",
            "nouvelle_note": "abc",
        },
    )

    assert response.status_code == 200


def test_ajouter_refuse_un_mode_invalide():
    client = app.app.test_client()

    response = client.post(
        "/ajouter",
        data={
            "mode": "invalide",
            "note": "15",
            "bareme": "20",
            "nouvelle_matiere": "Anglais",
            "coefficient": "3",
        },
    )

    assert response.status_code == 200
    assert b"Mode invalide." in response.data

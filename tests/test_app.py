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

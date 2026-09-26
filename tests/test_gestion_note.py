import pytest

import gestion_note
import sauvegarde


@pytest.fixture(autouse=True)
def etat_propre(monkeypatch):
    """
    Isole chaque test des donnees reelles et empeche l'ecriture
    dans notes.json.
    """
    notes_test = {}
    coef_test = {}

    monkeypatch.setattr(sauvegarde, "notes", notes_test)
    monkeypatch.setattr(sauvegarde, "coef", coef_test)
    monkeypatch.setattr(gestion_note, "notes", notes_test)
    monkeypatch.setattr(gestion_note, "coef", coef_test)
    monkeypatch.setattr(gestion_note, "sauvegarder", lambda: None)


def test_convertir_sur_20():
    assert gestion_note.convertir_sur_20({"note": 10, "bareme": 10}) == 20
    assert gestion_note.convertir_sur_20({"note": 5, "bareme": 20}) == 5


def test_calculer_moyenne():
    notes = [
        {"note": 10, "bareme": 10},
        {"note": 10, "bareme": 20},
    ]

    assert gestion_note.calculer_moyenne(notes) == 15


def test_calculer_moyenne_sans_note():
    assert gestion_note.calculer_moyenne([]) == 0


def test_ajouter_note_cree_une_matiere():
    gestion_note.ajouter_note("Maths", 15, 4)

    assert gestion_note.notes == {
        "Maths": [{"note": 15, "bareme": 20}]
    }
    assert gestion_note.coef == {"Maths": 4}


def test_ajouter_note_conserve_le_bareme():
    gestion_note.ajouter_note("Physique", 8, 3, 10)

    assert gestion_note.notes["Physique"] == [
        {"note": 8, "bareme": 10}
    ]


def test_ajouter_note_reconnait_une_matiere_existante():
    gestion_note.ajouter_note("Maths", 15, 4)
    gestion_note.ajouter_note("  maths  ", 12, 4)

    assert list(gestion_note.notes) == ["Maths"]
    assert gestion_note.notes["Maths"] == [
        {"note": 15, "bareme": 20},
        {"note": 12, "bareme": 20},
    ]


def test_ajouter_note_refuse_un_coefficient_different():
    gestion_note.ajouter_note("Maths", 15, 4)

    with pytest.raises(
        ValueError,
        match="coefficient 4",
    ):
        gestion_note.ajouter_note("Maths", 12, 5)


@pytest.mark.parametrize(
    ("note", "bareme"),
    [
        (-1, 20),
        (21, 20),
        (11, 10),
    ],
)
def test_ajouter_note_refuse_une_note_hors_bareme(note, bareme):
    with pytest.raises(ValueError):
        gestion_note.ajouter_note("Maths", note, 4, bareme)


@pytest.mark.parametrize("bareme", [0, 15, 30])
def test_ajouter_note_refuse_un_bareme_invalide(bareme):
    with pytest.raises(ValueError):
        gestion_note.ajouter_note("Maths", 10, 4, bareme)


def test_ajouter_note_refuse_une_matiere_vide():
    with pytest.raises(ValueError, match="ne peut pas être vide"):
        gestion_note.ajouter_note("   ", 10, 4)


def test_ajouter_note_refuse_un_coefficient_invalide():
    with pytest.raises(ValueError):
        gestion_note.ajouter_note("Maths", 10, 0)

    with pytest.raises(TypeError):
        gestion_note.ajouter_note("Maths", 10, 2.5)


def test_modifier_note():
    gestion_note.ajouter_note("Maths", 12, 4)

    gestion_note.modifier_note("Maths", 0, 16)

    assert gestion_note.notes["Maths"][0] == {
        "note": 16,
        "bareme": 20,
    }


def test_modifier_note_respecte_le_bareme():
    gestion_note.ajouter_note("Physique", 8, 3, 10)

    with pytest.raises(ValueError):
        gestion_note.modifier_note("Physique", 0, 11)


def test_modifier_note_refuse_un_index_invalide():
    gestion_note.ajouter_note("Maths", 12, 4)

    with pytest.raises(ValueError):
        gestion_note.modifier_note("Maths", 1, 15)


def test_supprimer_note():
    gestion_note.ajouter_note("Maths", 12, 4)
    gestion_note.ajouter_note("Maths", 16, 4)

    gestion_note.supprimer_note("Maths", 0)

    assert gestion_note.notes["Maths"] == [
        {"note": 16, "bareme": 20}
    ]


def test_supprimer_matiere():
    gestion_note.ajouter_note("Maths", 15, 4)

    gestion_note.supprimer_matiere("Maths")

    assert gestion_note.notes == {}
    assert gestion_note.coef == {}


def test_calculer_moyennes():
    gestion_note.ajouter_note("Maths", 15, 4)
    gestion_note.ajouter_note("Physique", 10, 2)

    moyennes, moyenne_generale = gestion_note.calculer_moyennes()

    assert moyennes == {
        "Maths": 15,
        "Physique": 10,
    }
    assert moyenne_generale == pytest.approx(13.3333333333)

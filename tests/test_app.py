import pytest

from calculateur import create_app


@pytest.fixture
def app():
    return create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-only-secret-key",
    })


def test_visitors_get_separate_browser_profiles(app):
    first = app.test_client()
    second = app.test_client()

    assert first.get("/").status_code == 200
    assert second.get("/").status_code == 200
    assert first.get("/api/etat").get_json() == {"notes": {}, "coef": {}}
    assert second.get("/api/etat").get_json() == {"notes": {}, "coef": {}}

    payload = {
        "notes": {"Maths": [{"note": 15, "bareme": 20}]},
        "coef": {"Maths": 4},
    }
    saved = first.post("/api/synchroniser", json=payload, headers={"If-Match": '"1"'})

    assert saved.status_code == 200
    assert saved.get_json() == payload
    assert saved.headers["ETag"] == '"2"'
    assert first.get("/api/etat").get_json() == payload
    assert second.get("/api/etat").get_json() == {"notes": {}, "coef": {}}


def test_stale_version_returns_conflict_without_overwriting_newer_state(app):
    client = app.test_client()
    first_state = {
        "notes": {"Maths": [{"note": 15, "bareme": 20}]},
        "coef": {"Maths": 3},
    }
    stale_state = {
        "notes": {"Maths": [{"note": 8, "bareme": 10}]},
        "coef": {"Maths": 3},
    }

    assert client.post(
        "/api/synchroniser",
        json=first_state,
        headers={"If-Match": '"1"'},
    ).status_code == 200

    stale = client.post(
        "/api/synchroniser",
        json=stale_state,
        headers={"If-Match": '"1"'},
    )

    assert stale.status_code == 409
    assert stale.get_json()["data"] == first_state
    assert stale.get_json()["version"] == 2
    assert client.get("/api/etat").get_json() == first_state


def test_invalid_data_is_rejected_without_changing_cache(app):
    client = app.test_client()
    initial = client.get("/api/etat").get_json()

    response = client.post(
        "/api/synchroniser",
        json={
            "notes": {"Maths": [{"note": 25, "bareme": 20}]},
            "coef": {"Maths": 4},
        },
        headers={"If-Match": '"1"'},
    )

    assert response.status_code == 400
    assert client.get("/api/etat").get_json() == initial


def test_pages_are_served_without_database(app):
    client = app.test_client()

    for path in ("/", "/ajouter", "/notes", "/tableur"):
        response = client.get(path)
        assert response.status_code == 200

    assert "sqlalchemy" not in app.extensions
    assert "migrate" not in app.extensions
    assert "gradebook_repository" in app.extensions


def test_admin_is_retained_as_disabled_status_page(app):
    client = app.test_client()

    response = client.get("/admin")

    assert response.status_code == 503
    page = response.get_data(as_text=True)
    assert "Espace administrateur" in page
    assert "Fonctionnalité non fonctionnelle" in page
    assert "Aucun profil centralisé" in page
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "path",
    (
        "/admin/connexion",
        "/admin/deconnexion",
        "/admin/export.json",
        "/admin/utilisateur/1",
        "/admin/utilisateur/1/supprimer",
    ),
)
def test_admin_data_routes_are_not_registered(app, path):
    assert app.test_client().get(path).status_code == 404


def test_memory_cache_can_be_rehydrated_after_process_restart():
    secret = "test-only-secret-key"
    old_app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": secret,
    })
    old_client = old_app.test_client()
    payload = {
        "notes": {"Physique": [{"note": 16, "bareme": 20}]},
        "coef": {"Physique": 3},
    }
    old_client.post(
        "/api/synchroniser",
        json=payload,
        headers={"If-Match": '"1"'},
    )

    cookie = old_client.get_cookie("session")
    new_app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": secret,
    })
    new_client = new_app.test_client()
    new_client.set_cookie("session", cookie.value)

    # Le nouveau processus a un cache vide ; le navigateur peut le réhydrater.
    assert new_client.get("/api/etat").get_json() == {"notes": {}, "coef": {}}
    restored = new_client.post(
        "/api/synchroniser",
        json=payload,
        headers={"If-Match": '"1"'},
    )
    assert restored.status_code == 200
    assert restored.get_json() == payload

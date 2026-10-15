import os
import app as module


def reset_database():
    with module.app.app_context():
        module.db.drop_all()
        module.db.create_all()


def test_visitors_get_separate_automatic_profiles():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    with module.app.test_client() as first, module.app.test_client() as second:
        assert first.get("/").status_code == 200
        assert second.get("/").status_code == 200
        first_state = first.get("/api/etat").get_json()
        second_state = second.get("/api/etat").get_json()
        assert first_state == {"notes": {}, "coef": {}}
        assert second_state == {"notes": {}, "coef": {}}
        first.post("/api/synchroniser", json={
            "notes": {"Maths": [{"note": 15, "bareme": 20}]},
            "coef": {"Maths": 4},
        })
        assert first.get("/api/etat").get_json()["notes"]["Maths"][0]["note"] == 15
        assert second.get("/api/etat").get_json() == {"notes": {}, "coef": {}}


def test_admin_requires_authentication(monkeypatch):
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "long-test-admin-password")
    reset_database()
    with module.app.test_client() as client:
        assert client.get("/admin").status_code == 302
        response = client.post("/admin/connexion", data={
            "email": "admin@example.com",
            "password": "long-test-admin-password",
        })
        assert response.status_code == 302
        assert client.get("/admin").status_code == 200


def test_invalid_data_is_rejected():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    with module.app.test_client() as client:
        response = client.post("/api/synchroniser", json={
            "notes": {"Maths": [{"note": 25, "bareme": 20}]},
            "coef": {"Maths": 4},
        })
        assert response.status_code == 400

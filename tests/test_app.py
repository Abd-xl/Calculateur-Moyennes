import app as module


def reset_database():
    with module.app.app_context():
        module.db.drop_all()
        module.db.create_all()


def test_visitors_get_separate_automatic_profiles():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    # Ne pas imbriquer deux clients Flask avec des contextes préservés :
    # leurs piles de contexte peuvent se fermer dans le mauvais ordre.
    first = module.app.test_client()
    second = module.app.test_client()
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



def test_admin_login_rate_limit_is_per_ip(monkeypatch):
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "long-test-admin-password")
    reset_database()

    with module.app.test_client() as client:
        for _ in range(5):
            response = client.post(
                "/admin/connexion",
                data={"email": "wrong@example.com", "password": "wrong-password"},
                headers={"X-Forwarded-For": "198.51.100.10, 10.0.0.1"},
            )
            assert response.status_code == 200

        blocked = client.post(
            "/admin/connexion",
            data={"email": "wrong@example.com", "password": "wrong-password"},
            headers={"X-Forwarded-For": "198.51.100.10, 10.0.0.1"},
        )
        assert blocked.status_code == 429

        # Une autre IP cliente ne doit pas hériter du blocage de la première.
        other_ip = client.post(
            "/admin/connexion",
            data={"email": "wrong@example.com", "password": "wrong-password"},
            headers={"X-Forwarded-For": "198.51.100.11, 10.0.0.1"},
        )
        assert other_ip.status_code == 200

def test_invalid_data_is_rejected():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    with module.app.test_client() as client:
        response = client.post("/api/synchroniser", json={
            "notes": {"Maths": [{"note": 25, "bareme": 20}]},
            "coef": {"Maths": 4},
        })
        assert response.status_code == 400

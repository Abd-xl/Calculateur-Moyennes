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

def test_initial_sync_persists_browser_data_and_marks_profile_initialized():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    payload = {
        "notes": {"Maths": [{"note": 15, "bareme": 20}]},
        "coef": {"Maths": 4},
    }

    with module.app.test_client() as client:
        assert client.get("/").status_code == 200
        with module.app.app_context():
            visitor = module.Visitor.query.first()
            assert visitor is not None
            assert visitor.data_initialized is False

        response = client.post("/api/synchroniser", json=payload)
        assert response.status_code == 200
        assert response.get_json() == payload

        # Vérifier l'état persisté dans la base, puis le relire lors d'une requête distincte.
        with module.app.app_context():
            module.db.session.expire_all()
            visitor = module.Visitor.query.first()
            assert visitor.data == payload
            assert visitor.data_initialized is True
        assert client.get("/api/etat").get_json() == payload


def test_empty_initial_sync_marks_profile_initialized():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    empty_state = {"notes": {}, "coef": {}}

    with module.app.test_client() as client:
        assert client.post("/api/synchroniser", json=empty_state).status_code == 200
        with module.app.app_context():
            visitor = module.Visitor.query.first()
            assert visitor is not None
            assert visitor.data == empty_state
            assert visitor.data_initialized is True


def test_invalid_sync_does_not_mark_profile_initialized_or_overwrite_data():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    with module.app.test_client() as client:
        client.get("/")
        with module.app.app_context():
            visitor = module.Visitor.query.first()
            assert visitor.data_initialized is False
            original_data = dict(visitor.data)

        response = client.post("/api/synchroniser", json={
            "notes": {"Maths": [{"note": 25, "bareme": 20}]},
            "coef": {"Maths": 4},
        })

        assert response.status_code == 400
        with module.app.app_context():
            module.db.session.expire_all()
            visitor = module.Visitor.query.first()
            assert visitor.data == original_data
            assert visitor.data_initialized is False



def test_admin_dashboard_renders_search_cards_and_summary(monkeypatch):
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "long-test-admin-password")
    reset_database()

    with module.app.test_client() as client:
        client.post("/admin/connexion", data={
            "email": "admin@example.com",
            "password": "long-test-admin-password",
        })
        response = client.get("/admin")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'id="visitor-search"' in page
        assert 'class="admin-stats"' in page
        assert 'class="admin-cards"' in page
        assert 'class="admin-table-wrap"' in page
        assert "Exporter JSON" in page
        admin_css = client.get("/static/admin.css")
        assert admin_css.status_code == 200
        assert ".admin-page" in admin_css.get_data(as_text=True)


def test_admin_visitor_detail_renders_profile_metadata(monkeypatch):
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "long-test-admin-password")
    reset_database()

    with module.app.app_context():
        visitor = module.Visitor(
            public_id="visitor-test-id",
            token_hash="a" * 64,
            browser_info="Test browser",
            data={"notes": {"Maths": [{"note": 15, "bareme": 20}]}, "coef": {"Maths": 4}},
            data_initialized=True,
        )
        module.db.session.add(visitor)
        module.db.session.commit()
        visitor_id = visitor.id

    with module.app.test_client() as client:
        client.post("/admin/connexion", data={
            "email": "admin@example.com",
            "password": "long-test-admin-password",
        })
        response = client.get(f"/admin/utilisateur/{visitor_id}")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert "visitor-test-id" in page
        assert "Test browser" in page
        assert "Maths" in page
        assert "15/20" in page

def test_public_routes_remain_available_after_refactor():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()

    assert {"public", "admin"}.issubset(module.app.blueprints)
    with module.app.test_client() as client:
        for path in ("/", "/ajouter", "/notes", "/tableur", "/api/etat"):
            response = client.get(path)
            assert response.status_code == 200, path


def test_admin_missing_visitor_renders_custom_404(monkeypatch):
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "long-test-admin-password")
    reset_database()

    with module.app.test_client() as client:
        client.post("/admin/connexion", data={
            "email": "admin@example.com",
            "password": "long-test-admin-password",
        })
        response = client.get("/admin/utilisateur/999999")
        assert response.status_code == 404
        assert "Retour au calculateur" in response.get_data(as_text=True)


def test_admin_export_remains_protected_and_returns_json(monkeypatch):
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "long-test-admin-password")
    reset_database()

    with module.app.test_client() as client:
        assert client.get("/admin/export.json").status_code == 302
        client.post("/admin/connexion", data={
            "email": "admin@example.com",
            "password": "long-test-admin-password",
        })
        response = client.get("/admin/export.json")
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        assert response.headers["Content-Disposition"].startswith("attachment;")

def test_public_actions_reject_negative_note_indexes():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    payload = {
        "notes": {
            "Maths": [
                {"note": 12, "bareme": 20},
                {"note": 15, "bareme": 20},
            ]
        },
        "coef": {"Maths": 4},
    }

    with module.app.test_client() as client:
        assert client.get("/").status_code == 200
        assert client.post("/api/synchroniser", json=payload).status_code == 200

        modified = client.post("/modifier", data={
            "matiere": "Maths",
            "index": "-1",
            "nouvelle_note": "19",
        })
        assert modified.status_code == 302
        assert client.get("/api/etat").get_json() == payload

        deleted = client.post("/supprimer", data={
            "matiere": "Maths",
            "index": "-1",
        })
        assert deleted.status_code == 302
        assert client.get("/api/etat").get_json() == payload

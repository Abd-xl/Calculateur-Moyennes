import app as module
from calculateur.repositories.visitor_gradebook import save_gradebook
from calculateur.services.gradebook_audit import audit_gradebooks


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


def test_stale_sync_returns_conflict_and_preserves_the_newer_state():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    first_state = {
        "notes": {"Maths": [{"note": 15, "bareme": 20}]},
        "coef": {"Maths": 3},
    }
    stale_state = {
        "notes": {"Maths": [{"note": 8, "bareme": 10}]},
        "coef": {"Maths": 3},
    }

    with module.app.test_client() as client:
        client.get("/")
        first = client.post(
            "/api/synchroniser", json=first_state, headers={"If-Match": '"1"'}
        )
        assert first.status_code == 200
        assert first.headers["ETag"] == '"2"'

        stale = client.post(
            "/api/synchroniser", json=stale_state, headers={"If-Match": '"1"'}
        )
        assert stale.status_code == 409
        assert stale.get_json()["data"] == first_state
        assert stale.get_json()["version"] == 2
        with module.app.app_context():
            visitor = module.Visitor.query.first()
            assert visitor.data == first_state
            assert visitor.gradebook_version == 2



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
        assert 'name="q"' in page
        assert 'method="get"' in page
        assert 'class="admin-stats"' in page
        assert 'class="admin-cards"' in page
        assert 'class="admin-table-wrap"' in page
        assert "Exporter JSON" in page


def test_admin_dashboard_filters_and_paginates_in_database(monkeypatch):
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "long-test-admin-password")
    reset_database()
    with module.app.app_context():
        module.db.session.add_all(
            [
                module.Visitor(
                    public_id=f"visitor-{index}",
                    token_hash=f"token-{index}",
                    browser_info="unique browser" if index == 25 else "browser",
                    data={"notes": {}, "coef": {}},
                )
                for index in range(26)
            ]
        )
        module.db.session.commit()

    with module.app.test_client() as client:
        client.post("/admin/connexion", data={
            "email": "admin@example.com",
            "password": "long-test-admin-password",
        })
        first_page = client.get("/admin")
        assert first_page.status_code == 200
        assert "Page 1 sur 2" in first_page.get_data(as_text=True)
        second_page = client.get("/admin?page=2")
        assert "Page 2 sur 2" in second_page.get_data(as_text=True)
        filtered = client.get("/admin?q=unique%20browser")
        assert "1 résultat(s)" in filtered.get_data(as_text=True)


def test_gradebook_audit_accepts_matching_legacy_and_relational_data():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    data = {
        "notes": {
            "Maths": [{"note": 15, "bareme": 20}, {"note": 8, "bareme": 10}],
            "Physique": [{"note": 12, "bareme": 20}],
        },
        "coef": {"Maths": 3, "Physique": 2},
    }
    with module.app.app_context():
        visitor = module.Visitor(
            public_id="audit-profile",
            token_hash="audit-token",
            data=data,
        )
        module.db.session.add(visitor)
        module.db.session.flush()
        save_gradebook(visitor, data, module.db.session, expected_version=1)

        report = audit_gradebooks(module.db.session, batch_size=1)
        assert report["profiles"] == 1
        assert report["legacy_subjects"] == report["relational_subjects"] == 2
        assert report["legacy_grades"] == report["relational_grades"] == 3
        assert report["issue_count"] == 0


def test_gradebook_audit_reports_json_mismatch():
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    reset_database()
    relational = {"notes": {"Maths": [{"note": 15, "bareme": 20}]}, "coef": {"Maths": 3}}
    legacy = {"notes": {"Maths": [{"note": 14, "bareme": 20}]}, "coef": {"Maths": 3}}
    with module.app.app_context():
        visitor = module.Visitor(
            public_id="mismatch-profile",
            token_hash="mismatch-token",
            data=relational,
        )
        module.db.session.add(visitor)
        module.db.session.flush()
        save_gradebook(visitor, relational, module.db.session, expected_version=1)
        visitor.data = legacy
        module.db.session.commit()

        report = audit_gradebooks(module.db.session)
        assert report["profiles_with_issues"] == 1
        assert report["issue_count"] >= 2


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
        assert response.headers["Cache-Control"] == "no-store"
        page = response.get_data(as_text=True)
        assert "visitor-test-id" in page
        assert "Test browser" in page
        assert "Maths" in page
        assert "15/20" in page
        export = client.get("/admin/export.json")
        assert export.status_code == 200
        assert export.headers["Cache-Control"] == "no-store"
        assert export.get_json()["visitors"][0]["anonymous_id"] == "visitor-test-id"


def test_admin_can_delete_visitor_and_cascaded_gradebook(monkeypatch):
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "long-test-admin-password")
    reset_database()
    data = {
        "notes": {"Maths": [{"note": 15, "bareme": 20}]},
        "coef": {"Maths": 4},
    }
    with module.app.app_context():
        visitor = module.Visitor(
            public_id="delete-profile",
            token_hash="delete-profile-token",
            data=data,
        )
        module.db.session.add(visitor)
        module.db.session.flush()
        save_gradebook(visitor, data, module.db.session, expected_version=1)
        visitor_id = visitor.id

    with module.app.test_client() as client:
        assert client.post(f"/admin/utilisateur/{visitor_id}/supprimer").status_code == 302
        client.post("/admin/connexion", data={
            "email": "admin@example.com",
            "password": "long-test-admin-password",
        })
        assert client.get(f"/admin/utilisateur/{visitor_id}/supprimer").status_code == 405
        response = client.post(f"/admin/utilisateur/{visitor_id}/supprimer")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/admin")

    with module.app.app_context():
        assert module.db.session.get(module.Visitor, visitor_id) is None
        assert module.Subject.query.count() == 0
        assert module.Grade.query.count() == 0

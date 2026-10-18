from datetime import datetime
import importlib.util
import json
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

import app as app_module
from calculateur.extensions import db
from calculateur.models import Visitor
from calculateur.startup_migration import migrate_and_audit_database


MIGRATION_PATH = (
    Path(__file__).parents[1] / "migrations" / "versions" / "0001_relational_gradebook.py"
)
SPEC = importlib.util.spec_from_file_location("gradebook_migration", MIGRATION_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


def _legacy_database():
    engine = sa.create_engine("sqlite:///:memory:")
    metadata = sa.MetaData()
    visitors = sa.Table(
        "anonymous_visitors",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("browser_info", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("last_seen_at", sa.DateTime, nullable=False),
        sa.Column("data", sa.JSON, nullable=False),
    )
    metadata.create_all(engine)
    return engine, visitors


def _run_upgrade(connection):
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        MIGRATION.upgrade()


def test_migration_validates_all_profiles_before_changing_schema():
    engine, visitors = _legacy_database()
    valid = {"notes": {"Maths": [{"note": 15, "bareme": 20}]}, "coef": {"Maths": 3}}
    invalid = {"notes": {"Maths": [{"note": 25, "bareme": 20}]}, "coef": {"Maths": 3}}
    with engine.begin() as connection:
        connection.execute(
            visitors.insert(),
            [
                {
                    "id": 1,
                    "public_id": "valid",
                    "token_hash": "a",
                    "browser_info": "test",
                    "created_at": datetime(2026, 1, 1),
                    "last_seen_at": datetime(2026, 1, 1),
                    "data": valid,
                },
                {
                    "id": 2,
                    "public_id": "invalid",
                    "token_hash": "b",
                    "browser_info": "test",
                    "created_at": datetime(2026, 1, 1),
                    "last_seen_at": datetime(2026, 1, 1),
                    "data": invalid,
                },
            ],
        )
        with pytest.raises(RuntimeError, match="Profil 2"):
            _run_upgrade(connection)
        assert "subjects" not in sa.inspect(connection).get_table_names()
        assert "grades" not in sa.inspect(connection).get_table_names()
        assert "data_initialized" not in {
            column["name"] for column in sa.inspect(connection).get_columns("anonymous_visitors")
        }
        assert connection.scalar(sa.select(sa.func.count()).select_from(visitors)) == 2
    engine.dispose()


def test_migration_copies_valid_profiles_and_keeps_legacy_json():
    engine, visitors = _legacy_database()
    data = {
        "notes": {"Maths": [{"note": 15, "bareme": 20}], "Physique": []},
        "coef": {"Maths": 3, "Physique": 2},
    }
    with engine.begin() as connection:
        connection.execute(
            visitors.insert().values(
                id=1,
                public_id="valid",
                token_hash="a",
                browser_info="test",
                created_at=datetime(2026, 1, 1),
                last_seen_at=datetime(2026, 1, 1),
                data=data,
            )
        )
        _run_upgrade(connection)
        assert connection.scalar(sa.text("SELECT count(*) FROM subjects")) == 2
        assert connection.scalar(sa.text("SELECT count(*) FROM grades")) == 1
        assert connection.scalar(
            sa.select(visitors.c.data).where(visitors.c.id == 1)
        ) == data
    engine.dispose()


def _legacy_application_database(data):
    app_module.app.config.update(TESTING=True, AUTO_CREATE_DB=False)
    with app_module.app.app_context():
        db.drop_all()
        with db.engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")
            connection.exec_driver_sql(
                """
                CREATE TABLE anonymous_visitors (
                    id INTEGER PRIMARY KEY,
                    public_id VARCHAR(36) NOT NULL UNIQUE,
                    token_hash VARCHAR(64) NOT NULL UNIQUE,
                    browser_info VARCHAR(512) NOT NULL,
                    created_at DATETIME NOT NULL,
                    last_seen_at DATETIME NOT NULL,
                    data JSON NOT NULL
                )
                """
            )
            connection.execute(
                sa.text(
                    """INSERT INTO anonymous_visitors
                       (id, public_id, token_hash, browser_info, created_at,
                        last_seen_at, data)
                       VALUES (1, 'public-id', 'token-hash', 'test',
                               CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :data)"""
                ),
                {"data": json.dumps(data)},
            )


def test_startup_migration_converts_and_audits_legacy_profile():
    data = {
        "notes": {"Maths": [{"note": 15, "bareme": 20}]},
        "coef": {"Maths": 3},
    }
    _legacy_application_database(data)

    migrate_and_audit_database(app_module.app)

    with app_module.app.app_context():
        visitor = db.session.get(Visitor, 1)
        assert visitor.data == data
        assert visitor.data_initialized is False
        assert [(subject.name, subject.coefficient) for subject in visitor.subjects] == [
            ("Maths", 3)
        ]
        assert [grade.value for grade in visitor.subjects[0].grades] == [15]


def test_startup_preflight_failure_leaves_legacy_schema_untouched():
    invalid = {"notes": {"Maths": [{"note": 25, "bareme": 20}]}, "coef": {"Maths": 3}}
    _legacy_application_database(invalid)

    with pytest.raises(RuntimeError, match="annulée avant toute écriture"):
        migrate_and_audit_database(app_module.app)

    with app_module.app.app_context():
        tables = sa.inspect(db.engine).get_table_names()
        assert "subjects" not in tables
        assert "grades" not in tables
        assert "data_initialized" not in {
            column["name"]
            for column in sa.inspect(db.engine).get_columns("anonymous_visitors")
        }


def test_render_app_runs_migration_before_returning(monkeypatch):
    from calculateur import create_app
    import calculateur.startup_migration as startup_migration

    migrated_apps = []
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("SECRET_KEY", "test-render-secret")
    monkeypatch.setattr(
        startup_migration,
        "migrate_and_audit_database",
        migrated_apps.append,
    )

    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})

    assert migrated_apps == [app]


def test_auto_migration_can_be_disabled_explicitly(monkeypatch):
    from calculateur import create_app
    import calculateur.startup_migration as startup_migration

    migrated_apps = []
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("SECRET_KEY", "test-render-secret")
    monkeypatch.setattr(
        startup_migration,
        "migrate_and_audit_database",
        migrated_apps.append,
    )

    create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "AUTO_MIGRATE_DB": False,
        }
    )

    assert migrated_apps == []

from datetime import datetime
import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


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

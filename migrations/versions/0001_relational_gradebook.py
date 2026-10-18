"""Add relational subjects and grades, copying the legacy visitor JSON.

Revision ID: 0001_relational_gradebook
Revises:
Create Date: 2026-10-18
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "0001_relational_gradebook"
down_revision = None
branch_labels = None
depends_on = None


def _ensure_visitor_table(bind):
    inspector = sa.inspect(bind)
    if "anonymous_visitors" not in inspector.get_table_names():
        op.create_table(
            "anonymous_visitors",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("public_id", sa.String(length=36), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("browser_info", sa.String(length=512), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("data", sa.JSON(), nullable=False),
            sa.Column(
                "data_initialized",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
    else:
        columns = {column["name"] for column in inspector.get_columns("anonymous_visitors")}
        if "data_initialized" not in columns:
            op.add_column(
                "anonymous_visitors",
                sa.Column(
                    "data_initialized",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                ),
            )

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("anonymous_visitors")}
    for name, column in (
        ("ix_anonymous_visitors_public_id", "public_id"),
        ("ix_anonymous_visitors_token_hash", "token_hash"),
    ):
        if name not in indexes:
            op.create_index(name, "anonymous_visitors", [column], unique=True)


def _decode_data(value, visitor_id):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Profil {visitor_id}: le champ data ne contient pas de JSON valide."
            ) from error
    if not isinstance(value, dict):
        raise RuntimeError(f"Profil {visitor_id}: le champ data n'est pas un objet JSON.")
    notes = value.get("notes")
    coefficients = value.get("coef")
    if not isinstance(notes, dict) or not isinstance(coefficients, dict):
        raise RuntimeError(f"Profil {visitor_id}: données notes/coef invalides.")
    if set(notes) != set(coefficients):
        raise RuntimeError(f"Profil {visitor_id}: matières et coefficients divergent.")
    return notes, coefficients


def upgrade():
    bind = op.get_bind()
    _ensure_visitor_table(bind)

    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("visitor_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("coefficient", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("coefficient > 0", name="ck_subject_coefficient_positive"),
        sa.ForeignKeyConstraint(
            ["visitor_id"], ["anonymous_visitors.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("visitor_id", "name", name="uq_subject_visitor_name"),
    )
    op.create_index("ix_subjects_visitor_id", "subjects", ["visitor_id"])

    op.create_table(
        "grades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("scale", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("scale IN (10, 20)", name="ck_grade_scale_valid"),
        sa.CheckConstraint("value >= 0", name="ck_grade_value_nonnegative"),
        sa.CheckConstraint("value <= scale", name="ck_grade_value_within_scale"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("subject_id", "position", name="uq_grade_subject_position"),
    )
    op.create_index("ix_grades_subject_id", "grades", ["subject_id"])

    visitors = sa.table(
        "anonymous_visitors",
        sa.column("id", sa.Integer()),
        sa.column("data", sa.JSON()),
    )
    subjects = sa.table(
        "subjects",
        sa.column("id", sa.Integer()),
        sa.column("visitor_id", sa.Integer()),
        sa.column("name", sa.Text()),
        sa.column("coefficient", sa.Integer()),
        sa.column("position", sa.Integer()),
    )
    grades = sa.table(
        "grades",
        sa.column("subject_id", sa.Integer()),
        sa.column("value", sa.Float()),
        sa.column("scale", sa.Integer()),
        sa.column("position", sa.Integer()),
    )

    for visitor in bind.execute(sa.select(visitors.c.id, visitors.c.data)).mappings():
        notes, coefficients = _decode_data(visitor["data"], visitor["id"])
        for subject_position, (name, subject_notes) in enumerate(notes.items()):
            if not isinstance(name, str) or not name.strip() or not isinstance(subject_notes, list):
                raise RuntimeError(f"Profil {visitor['id']}: matière invalide.")
            coefficient = coefficients[name]
            if isinstance(coefficient, bool) or not isinstance(coefficient, int) or coefficient <= 0:
                raise RuntimeError(f"Profil {visitor['id']}: coefficient invalide pour {name!r}.")
            result = bind.execute(
                subjects.insert().values(
                    visitor_id=visitor["id"],
                    name=name,
                    coefficient=coefficient,
                    position=subject_position,
                )
            )
            subject_id = result.inserted_primary_key[0]
            for grade_position, grade in enumerate(subject_notes):
                if not isinstance(grade, dict) or set(grade) != {"note", "bareme"}:
                    raise RuntimeError(f"Profil {visitor['id']}: note mal structurée en {name!r}.")
                value, scale = grade.get("note"), grade.get("bareme")
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or isinstance(scale, bool)
                    or scale not in (10, 20)
                    or not 0 <= value <= scale
                ):
                    raise RuntimeError(f"Profil {visitor['id']}: note invalide en {name!r}.")
                bind.execute(
                    grades.insert().values(
                        subject_id=subject_id,
                        value=value,
                        scale=scale,
                        position=grade_position,
                    )
                )


def downgrade():
    op.drop_index("ix_grades_subject_id", table_name="grades")
    op.drop_table("grades")
    op.drop_index("ix_subjects_visitor_id", table_name="subjects")
    op.drop_table("subjects")
    # Keep anonymous_visitors and its synchronized JSON payload as the rollback format.

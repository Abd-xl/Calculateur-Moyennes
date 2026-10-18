"""Add optimistic concurrency version for each visitor gradebook.

Revision ID: 0002_gradebook_version
Revises: 0001_relational_gradebook
Create Date: 2026-10-18
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_gradebook_version"
down_revision = "0001_relational_gradebook"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "anonymous_visitors",
        sa.Column("gradebook_version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade():
    op.drop_column("anonymous_visitors", "gradebook_version")

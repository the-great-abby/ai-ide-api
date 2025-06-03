"""add bug_reports table for in-app bug reporting

Revision ID: d4034974e03f
Revises: 030f81916b11
Create Date: 2025-05-17 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "d4034974e03f"
down_revision: Union[str, None] = "030f81916b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    # Only create the table if it doesn't exist
    if "bug_reports" not in inspector.get_table_names():
        op.create_table(
            "bug_reports",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("description", sa.Text()),
            sa.Column("reporter", sa.String()),
            sa.Column("page", sa.String()),
            sa.Column("timestamp", sa.DateTime()),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("bug_reports")

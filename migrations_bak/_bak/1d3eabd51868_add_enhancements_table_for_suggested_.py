"""add enhancements table for suggested improvements

Revision ID: 1d3eabd51868
Revises: d4034974e03f
Create Date: 2025-05-17 11:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "1d3eabd51868"
down_revision: Union[str, None] = "d4034974e03f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    # Only create the table if it doesn't exist
    if "enhancements" not in inspector.get_table_names():
        op.create_table(
            "enhancements",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("description", sa.Text()),
            sa.Column("suggested_by", sa.String()),
            sa.Column("page", sa.String()),
            sa.Column("tags", sa.String()),
            sa.Column("categories", sa.String()),
            sa.Column("timestamp", sa.DateTime()),
            sa.Column("proposal_id", sa.String()),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("enhancements")

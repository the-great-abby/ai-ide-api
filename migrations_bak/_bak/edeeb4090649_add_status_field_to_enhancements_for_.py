"""add status field to enhancements for transfer tracking

Revision ID: edeeb4090649
Revises: 1d3eabd51868
Create Date: 2025-05-17 11:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "edeeb4090649"
down_revision: Union[str, None] = "1d3eabd51868"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    # Only add the column if it doesn't exist
    if "enhancements" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("enhancements")]
        if "status" not in columns:
            op.add_column(
                "enhancements", sa.Column("status", sa.String(), nullable=True)
            )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("enhancements", "status")

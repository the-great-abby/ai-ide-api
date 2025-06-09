"""add project_id to memory_vectors

Revision ID: a2b3c4d5e6f7_memvec_project
Revises: None  # Updated: removed a1b2c3d4e5f6_projmem, which was deleted
Create Date: 2025-05-18 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7_memvec_project"
down_revision: Union[str, None] = None  # Updated: removed a1b2c3d4e5f6_projmem, which was deleted
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "memory_vectors" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("memory_vectors")]
        if "project_id" not in columns:
            op.add_column(
                "memory_vectors", sa.Column("project_id", sa.String(), nullable=True)
            )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("memory_vectors", "project_id")

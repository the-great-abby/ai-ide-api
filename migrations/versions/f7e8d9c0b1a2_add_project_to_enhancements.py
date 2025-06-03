"""
Add project to enhancements

Revision ID: f7e8d9c0b1a2
Revises: e1f2a3b4c5d6
Create Date: 2025-05-17 11:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "f7e8d9c0b1a2"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "enhancements" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("enhancements")]
        if "project" not in columns:
            op.add_column("enhancements", sa.Column("project", sa.String(length=255)))


def downgrade() -> None:
    op.drop_column("enhancements", "project")

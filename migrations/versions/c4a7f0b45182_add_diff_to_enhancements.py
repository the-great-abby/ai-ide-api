"""add diff to enhancements

Revision ID: c4a7f0b45182
Revises: 98d34407c6f1
Create Date: 2025-05-15 15:43:20.369488

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "c4a7f0b45182"
down_revision: Union[str, None] = "98d34407c6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    # Add diff to enhancements if not exists
    if "enhancements" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("enhancements")]
        if "diff" not in columns:
            op.add_column("enhancements", sa.Column("diff", sa.Text(), nullable=True))
    # Add user_story to rule_versions if not exists
    if "rule_versions" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("rule_versions")]
        if "user_story" not in columns:
            op.add_column(
                "rule_versions", sa.Column("user_story", sa.Text(), nullable=True)
            )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("rule_versions", "user_story")
    op.drop_column("enhancements", "diff")

"""empty message

Revision ID: 98d34407c6f1
Revises: c77f4c2517b0
Create Date: 2025-05-15 12:04:26.505969

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "98d34407c6f1"
down_revision: Union[str, None] = '7728045323ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    # Add user_story to rules if not exists
    if "rules" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("rules")]
        if "user_story" not in columns:
            op.add_column("rules", sa.Column("user_story", sa.Text(), nullable=True))

    # All proposals-related op.add_column and op.drop_column have been removed; these columns are now created in the consolidated migration.


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("rules", "user_story")

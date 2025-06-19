"""create test_table

Revision ID: d7f1630c88dc
Revises: 23b59ec9a17b
Create Date: 2025-06-13 01:07:51.266363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7f1630c88dc"
down_revision: Union[str, None] = "23b59ec9a17b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table("test_table", sa.Column("id", sa.String(), primary_key=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("test_table")

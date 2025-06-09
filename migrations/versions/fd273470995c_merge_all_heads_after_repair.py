"""merge all heads after repair

Revision ID: fd273470995c
Revises: None  # Updated: removed df7cfdab0f0e_create_test_table, which was deleted during migration consolidation. This is now the base migration after cleanup.
Create Date: 2025-06-06 12:02:24.430397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd273470995c'
down_revision: Union[str, None] = None  # Updated: removed df7cfdab0f0e_create_test_table, which was deleted. This is now the base.
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

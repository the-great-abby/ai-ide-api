"""Merge heads for project field migration

Revision ID: 326e17ceb7de
Revises: 20240512_add_project_to_enhancements, df6cfdab0f0e
Create Date: 2025-05-12 20:46:44.980933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '326e17ceb7de'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'df6cfdab0f0e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""Merge heads

Revision ID: c0f38afa30e4
Revises: 7e2b1a4c5f01, ab12cd34ef56
Create Date: 2025-05-14 02:53:08.837393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0f38afa30e4'
down_revision: Union[str, None] = ('7e2b1a4c5f01', 'ab12cd34ef56')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

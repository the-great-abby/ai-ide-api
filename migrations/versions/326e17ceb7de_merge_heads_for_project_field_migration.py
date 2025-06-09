"""Merge heads for project field migration

Revision ID: 326e17ceb7de
Revises: None  # Updated: removed df6cfdab0f0e, which was deleted
Create Date: 2025-05-12 20:46:44.980933

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "326e17ceb7de"
down_revision: Union[str, None] = None  # Updated: removed df6cfdab0f0e, which was deleted
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

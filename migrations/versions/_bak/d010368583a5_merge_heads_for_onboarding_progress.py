"""Merge heads for onboarding progress

Revision ID: d010368583a5
Revises: a0788ee96bea, b2e1c3d4f5a6
Create Date: 2025-05-19 19:46:06.388036

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd010368583a5'
down_revision: Union[str, None] = ('a0788ee96bea', 'b2e1c3d4f5a6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

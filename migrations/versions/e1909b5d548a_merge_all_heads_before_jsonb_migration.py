"""merge all heads before JSONB migration

Revision ID: e1909b5d548a
Revises: 8257e00862b4, merge_heads_20240614
Create Date: 2025-06-10 02:43:01.095289

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1909b5d548a'
down_revision: Union[str, None] = ('8257e00862b4', 'merge_heads_20240614')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

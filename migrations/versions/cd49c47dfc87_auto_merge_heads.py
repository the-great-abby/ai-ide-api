"""auto-merge heads

Revision ID: cd49c47dfc87
Revises: e1f2a3b4c5d6, dc83b8ed7bef
Create Date: 2025-05-13 12:24:12.129832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd49c47dfc87'
down_revision: Union[str, None] = ('e1f2a3b4c5d6', 'dc83b8ed7bef')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

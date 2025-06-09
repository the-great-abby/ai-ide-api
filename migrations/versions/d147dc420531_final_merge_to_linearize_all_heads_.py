"""Final merge to linearize all heads after feedback table fix

Revision ID: d147dc420531
Revises: 7754757c36c6, d6b2d533015b, fd273470995c
Create Date: 2025-06-06 20:46:58.827522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd147dc420531'
down_revision: Union[str, None] = ('7754757c36c6', 'd6b2d533015b', 'fd273470995c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

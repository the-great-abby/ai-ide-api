"""merge heads after fixing missing migration

Revision ID: 0e2e70527d19
Revises: abdfe1c4c174, d010368583a5
Create Date: 2025-05-21 04:51:24.994481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e2e70527d19'
down_revision: Union[str, None] = ('abdfe1c4c174', 'd010368583a5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

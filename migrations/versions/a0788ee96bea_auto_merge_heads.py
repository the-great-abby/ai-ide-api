"""auto merge heads

Revision ID: a0788ee96bea
Revises: 20240519_add_use_cases_table
Create Date: 2025-05-19 02:03:22.206875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0788ee96bea'
down_revision: Union[str, None] = '20240519_add_use_cases_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

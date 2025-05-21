"""merge_scope_fields_migrations

Revision ID: 8a41aeb0a5fb
Revises: bc451ac85c74, d912b78b75b4
Create Date: 2025-05-21 15:33:49.155716

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a41aeb0a5fb'
down_revision: Union[str, None] = ('bc451ac85c74', 'd912b78b75b4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

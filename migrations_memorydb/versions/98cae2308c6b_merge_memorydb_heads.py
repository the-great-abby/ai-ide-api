"""Merge memorydb heads

Revision ID: 98cae2308c6b
Revises: 20240525_add_proj_id_memvec, 20240527_fix_memory_vector_uuids
Create Date: 2025-06-03 12:21:01.520121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98cae2308c6b'
down_revision: Union[str, None] = ('20240525_add_proj_id_memvec', '20240527_fix_memory_vector_uuids')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

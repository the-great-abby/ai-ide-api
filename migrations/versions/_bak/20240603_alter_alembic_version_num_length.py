"""Alter alembic_version.version_num to VARCHAR(255) for long revision IDs

Revision ID: 20240603_alter_alembic_version_num_length
Revises: 0005_debug_side_effect
Create Date: 2024-06-03
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20240603_alter_alembic_version_num_length"
down_revision: Union[str, None] = "0005_debug_side_effect"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);")

def downgrade() -> None:
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(32);") 
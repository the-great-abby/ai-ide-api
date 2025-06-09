"""add hierarchical scope fields to rules, proposals, rule_versions

Revision ID: d912b78b75b4
Revises: d010368583a5
Create Date: 2025-05-21 00:54:25.770019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'd912b78b75b4'
down_revision: Union[str, None] = 'd010368583a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # All rules- and proposals-related op.add_column, op.create_index, and op.drop_column have been removed; these columns and indexes are now created in the consolidated migration. This migration is now a no-op.


def downgrade() -> None:
    """Downgrade schema."""
    # All rules- and proposals-related op.add_column, op.create_index, and op.drop_column have been removed; these columns and indexes are now created in the consolidated migration. This migration is now a no-op.

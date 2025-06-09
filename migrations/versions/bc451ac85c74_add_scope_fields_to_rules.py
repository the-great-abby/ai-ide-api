"""add_scope_fields_to_rules

Revision ID: bc451ac85c74
Revises: 0e2e70527d19
Create Date: 2025-05-21 05:04:44.284973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'bc451ac85c74'
down_revision: Union[str, None] = '0e2e70527d19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # All proposals- and rules-related op.add_column, op.create_index, and op.drop_column have been removed; these columns and indexes are now created in the consolidated migration. This migration is now a no-op.


def downgrade() -> None:
    """Downgrade schema."""
    # All proposals- and rules-related op.add_column, op.create_index, and op.drop_column have been removed; these columns and indexes are now created in the consolidated migration. This migration is now a no-op.

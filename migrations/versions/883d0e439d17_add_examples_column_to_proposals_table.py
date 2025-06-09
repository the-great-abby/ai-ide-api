"""Add examples column to proposals table

Revision ID: 883d0e439d17
Revises: bf9e065008bf
Create Date: 2025-05-13 11:44:55.030008

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "883d0e439d17"
down_revision: Union[str, None] = "bf9e065008bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # All rule_versions-related op.add_column and op.drop_column have been removed; these columns are now created in the consolidated migration.


def downgrade() -> None:
    """Downgrade schema."""
    # All rule_versions-related op.add_column and op.drop_column have been removed; these columns are now created in the consolidated migration.

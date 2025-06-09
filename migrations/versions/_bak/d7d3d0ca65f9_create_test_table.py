"""create test_table

Revision ID: d7d3d0ca65f9
Revises: 656e27e6240a
Create Date: 2025-06-05 15:52:28.055697

"""
from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7d3d0ca65f9'
down_revision: Union[str, None] = '656e27e6240a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    """Upgrade schema."""
    try:
        logger.info("DEBUG: Entering upgrade() in create_test_table migration")
        op.create_table(
            "test_table",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("note", sa.Text()),
        )
        logger.info("DEBUG: Successfully created test_table")
    except Exception as e:
        logger.error(f"ERROR in upgrade() create_test_table: {e}")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("test_table")

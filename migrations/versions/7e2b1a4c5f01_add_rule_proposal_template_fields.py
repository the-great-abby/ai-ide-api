"""
Add reason_for_change, references, and current_rule columns to proposals table

Revision ID: 7e2b1a4c5f01
Revises: None  # Updated: removed e1f2a3b4c5d6, which was deleted during migration consolidation
Create Date: 2024-06-13
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "7e2b1a4c5f01"
down_revision = None  # Updated: removed e1f2a3b4c5d6, which was deleted
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "proposals" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("proposals")]

        # All proposals-related op.add_column and op.drop_column have been removed; these columns are now created in the consolidated migration.
        pass


def downgrade():
    # All proposals-related op.add_column and op.drop_column have been removed; these columns are now created in the consolidated migration.
    pass

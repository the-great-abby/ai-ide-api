"""
Add reason_for_change, references, and current_rule columns to proposals table

Revision ID: 7e2b1a4c5f01
Revises: e1f2a3b4c5d6
Create Date: 2024-06-13
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "7e2b1a4c5f01"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "proposals" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("proposals")]

        # Add columns if they don't exist
        if "reason_for_change" not in columns:
            op.add_column(
                "proposals", sa.Column("reason_for_change", sa.Text(), nullable=True)
            )
        if "references" not in columns:
            op.add_column(
                "proposals", sa.Column("references", sa.Text(), nullable=True)
            )
        if "current_rule" not in columns:
            op.add_column(
                "proposals", sa.Column("current_rule", sa.Text(), nullable=True)
            )


def downgrade():
    op.drop_column("proposals", "reason_for_change")
    op.drop_column("proposals", "references")
    op.drop_column("proposals", "current_rule")

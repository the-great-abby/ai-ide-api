"""
Add applies_to and applies_to_rationale columns to rules, proposals, rule_versions, and enhancements tables

Revision ID: e1f2a3b4c5d6
Revises: edeeb4090649
Create Date: 2025-05-17 11:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "edeeb4090649"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    # Add applies_to to rules if not exists
    if "rules" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("rules")]
        if "applies_to" not in columns:
            op.add_column(
                "rules", sa.Column("applies_to", sa.String(), server_default="")
            )
        # Add applies_to_rationale to rules if not exists
        if "applies_to_rationale" not in columns:
            op.add_column(
                "rules",
                sa.Column("applies_to_rationale", sa.String(), server_default=""),
            )
    # Add applies_to to proposals if not exists
    if "proposals" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("proposals")]
        if "applies_to" not in columns:
            op.add_column(
                "proposals", sa.Column("applies_to", sa.String(), server_default="")
            )
        if "applies_to_rationale" not in columns:
            op.add_column(
                "proposals",
                sa.Column("applies_to_rationale", sa.String(), server_default=""),
            )
    # Add applies_to to rule_versions if not exists
    if "rule_versions" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("rule_versions")]
        if "applies_to" not in columns:
            op.add_column(
                "rule_versions", sa.Column("applies_to", sa.String(), server_default="")
            )
        if "applies_to_rationale" not in columns:
            op.add_column(
                "rule_versions",
                sa.Column("applies_to_rationale", sa.String(), server_default=""),
            )
    # Add applies_to to enhancements if not exists
    if "enhancements" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("enhancements")]
        if "applies_to" not in columns:
            op.add_column(
                "enhancements", sa.Column("applies_to", sa.String(), server_default="")
            )
        if "applies_to_rationale" not in columns:
            op.add_column(
                "enhancements",
                sa.Column("applies_to_rationale", sa.String(), server_default=""),
            )


def downgrade() -> None:
    op.drop_column("rules", "applies_to")
    op.drop_column("rules", "applies_to_rationale")
    op.drop_column("proposals", "applies_to")
    op.drop_column("proposals", "applies_to_rationale")
    op.drop_column("rule_versions", "applies_to")
    op.drop_column("rule_versions", "applies_to_rationale")
    op.drop_column("enhancements", "applies_to")
    op.drop_column("enhancements", "applies_to_rationale")

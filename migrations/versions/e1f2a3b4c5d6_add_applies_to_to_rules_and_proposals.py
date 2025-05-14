"""
Add applies_to and applies_to_rationale columns to rules, proposals, rule_versions, and enhancements tables

Revision ID: e1f2a3b4c5d6
Revises: edeeb4090649
Create Date: 2024-06-01
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e1f2a3b4c5d6"
down_revision = "edeeb4090649"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "rules", sa.Column("applies_to", sa.String(), nullable=True, server_default="")
    )
    op.add_column(
        "rules",
        sa.Column(
            "applies_to_rationale", sa.Text(), nullable=True, server_default=None
        ),
    )
    op.add_column(
        "proposals",
        sa.Column("applies_to", sa.String(), nullable=True, server_default=""),
    )
    op.add_column(
        "proposals",
        sa.Column(
            "applies_to_rationale", sa.Text(), nullable=True, server_default=None
        ),
    )
    op.add_column(
        "rule_versions",
        sa.Column("applies_to", sa.String(), nullable=True, server_default=""),
    )
    op.add_column(
        "rule_versions",
        sa.Column(
            "applies_to_rationale", sa.Text(), nullable=True, server_default=None
        ),
    )
    op.add_column(
        "enhancements",
        sa.Column("applies_to", sa.String(), nullable=True, server_default=""),
    )
    op.add_column(
        "enhancements",
        sa.Column(
            "applies_to_rationale", sa.Text(), nullable=True, server_default=None
        ),
    )


def downgrade():
    op.drop_column("rules", "applies_to")
    op.drop_column("rules", "applies_to_rationale")
    op.drop_column("proposals", "applies_to")
    op.drop_column("proposals", "applies_to_rationale")
    op.drop_column("rule_versions", "applies_to")
    op.drop_column("rule_versions", "applies_to_rationale")
    op.drop_column("enhancements", "applies_to")
    op.drop_column("enhancements", "applies_to_rationale")

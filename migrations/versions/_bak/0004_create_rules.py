"""create rules table

Revision ID: 0004_create_rules
Revises: 0003_create_rule_versions
Create Date: 2025-06-05

"""
from alembic import op
import sqlalchemy as sa

revision = '0004_create_rules'
down_revision = '0003_create_rule_versions'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "rules",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("rule_type", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("diff", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("submitted_by", sa.String(), nullable=True),
        sa.Column("added_by", sa.String(), nullable=True),
        sa.Column("project", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("categories", sa.String(), nullable=True),
        sa.Column("tags", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rules_added_by", "rules", ["added_by"], unique=False)
    op.create_index("ix_rules_id", "rules", ["id"], unique=False)
    op.create_index("ix_rules_project", "rules", ["project"], unique=False)
    op.create_index("ix_rules_rule_type", "rules", ["rule_type"], unique=False)
    op.create_index("ix_rules_submitted_by", "rules", ["submitted_by"], unique=False)

def downgrade():
    op.drop_index("ix_rules_submitted_by", table_name="rules")
    op.drop_index("ix_rules_rule_type", table_name="rules")
    op.drop_index("ix_rules_project", table_name="rules")
    op.drop_index("ix_rules_id", table_name="rules")
    op.drop_index("ix_rules_added_by", table_name="rules")
    op.drop_table("rules") 
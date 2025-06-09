"""create rule_versions table

Revision ID: 0003_create_rule_versions
Revises: 0002_create_proposals
Create Date: 2025-06-05

"""
from alembic import op
import sqlalchemy as sa

revision = '0003_create_rule_versions'
down_revision = '0002_create_proposals'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "rule_versions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("rule_id", sa.String(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("rule_type", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("diff", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("submitted_by", sa.String(), nullable=True),
        sa.Column("added_by", sa.String(), nullable=True),
        sa.Column("project", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("categories", sa.String(), nullable=True),
        sa.Column("tags", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rule_versions_id", "rule_versions", ["id"], unique=False)
    op.create_index("ix_rule_versions_rule_id", "rule_versions", ["rule_id"], unique=False)

def downgrade():
    op.drop_index("ix_rule_versions_rule_id", table_name="rule_versions")
    op.drop_index("ix_rule_versions_id", table_name="rule_versions")
    op.drop_table("rule_versions") 
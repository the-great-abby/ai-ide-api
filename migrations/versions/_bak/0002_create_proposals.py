"""create proposals table

Revision ID: 0002_create_proposals
Revises: 0001_create_feedback
Create Date: 2025-06-05

"""
from alembic import op
import sqlalchemy as sa

revision = '0002_create_proposals'
down_revision = '0001_create_feedback'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "proposals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("rule_type", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("diff", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("submitted_by", sa.String(), nullable=True),
        sa.Column("project", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("categories", sa.String(), nullable=True),
        sa.Column("tags", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proposals_id", "proposals", ["id"], unique=False)
    op.create_index("ix_proposals_project", "proposals", ["project"], unique=False)
    op.create_index("ix_proposals_rule_type", "proposals", ["rule_type"], unique=False)
    op.create_index("ix_proposals_submitted_by", "proposals", ["submitted_by"], unique=False)

def downgrade():
    op.drop_index("ix_proposals_submitted_by", table_name="proposals")
    op.drop_index("ix_proposals_rule_type", table_name="proposals")
    op.drop_index("ix_proposals_project", table_name="proposals")
    op.drop_index("ix_proposals_id", table_name="proposals")
    op.drop_table("proposals") 
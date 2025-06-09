"""create feedback table

Revision ID: 0001_create_feedback
Revises: 
Create Date: 2025-06-05

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_create_feedback'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedback') THEN DROP TYPE feedback; END IF; END $$;")
    op.create_table(
        "feedback",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("rule_id", sa.String(), nullable=True),
        sa.Column("project", sa.String(), nullable=True),
        sa.Column("feedback_type", sa.String(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("submitted_by", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feedback_id", "feedback", ["id"], unique=False)
    op.create_index("ix_feedback_project", "feedback", ["project"], unique=False)
    op.create_index("ix_feedback_rule_id", "feedback", ["rule_id"], unique=False)
    op.create_index("ix_feedback_submitted_by", "feedback", ["submitted_by"], unique=False)

def downgrade():
    op.drop_index("ix_feedback_submitted_by", table_name="feedback")
    op.drop_index("ix_feedback_rule_id", table_name="feedback")
    op.drop_index("ix_feedback_project", table_name="feedback")
    op.drop_index("ix_feedback_id", table_name="feedback")
    op.drop_table("feedback") 
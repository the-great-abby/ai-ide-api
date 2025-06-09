"""
Add use_cases table for collaborative use-case submissions

Revision ID: 20240519_add_use_cases_table
Revises: 99f48ac9b43d
Create Date: 2025-05-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20240519_add_use_cases_table'
down_revision = '99f48ac9b43d'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Only create the table if it doesn't exist
    if 'use_cases' not in inspector.get_table_names():
        op.create_table(
            "use_cases",
            sa.Column("id", sa.String(), primary_key=True, nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("example_workflow", sa.JSON(), nullable=False),
            sa.Column("tags", sa.String(length=255), nullable=True),
            sa.Column("categories", sa.String(length=255), nullable=True),
            sa.Column("submitted_by", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("source", sa.String(length=255), nullable=True),
        )
        op.create_index("ix_use_cases_status", "use_cases", ["status"])

def downgrade():
    op.drop_index("ix_use_cases_status", table_name="use_cases")
    op.drop_table("use_cases") 
"""
Add user_story column to enhancements table

Revision ID: add_user_story_to_enhancements
Revises: 
Create Date: 2024-06-01
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_user_story_to_enhancements"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "enhancements",
        sa.Column("user_story", sa.Text(), nullable=True, server_default=None)
    )

def downgrade():
    op.drop_column("enhancements", "user_story") 
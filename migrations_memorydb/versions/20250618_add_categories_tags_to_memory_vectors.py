"""Add categories and tags columns to memory_vectors

Revision ID: 20250618_add_categories_tags_to_memory_vectors
Revises: 20250617_remove_confidence_from_memory_vectors
Create Date: 2025-06-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20250618_add_categories_tags_to_memory_vectors"
down_revision = "20250617_remove_confidence_from_memory_vectors"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "memory_vectors",
        sa.Column(
            "categories",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="[]",
        ),
    )
    op.add_column(
        "memory_vectors",
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="[]",
        ),
    )


def downgrade():
    op.drop_column("memory_vectors", "categories")
    op.drop_column("memory_vectors", "tags")

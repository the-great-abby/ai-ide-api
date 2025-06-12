"""Add project_id column to memory_vectors

Revision ID: 20240525_add_proj_id_memvec
Revises: 20250518_create_memorydb_schema
Create Date: 2025-05-25

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "20240525_add_proj_id_memvec"
down_revision = "20250518_create_memorydb_schema"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if "memory_vectors" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("memory_vectors")]
        if "project_id" not in columns:
            op.add_column(
                "memory_vectors", sa.Column("project_id", sa.UUID(), nullable=True)
            )
            op.create_index(
                "ix_memory_vectors_project_id",
                "memory_vectors",
                ["project_id"],
                unique=False,
            )


def downgrade():
    op.drop_index("ix_memory_vectors_project_id", table_name="memory_vectors")
    op.drop_column("memory_vectors", "project_id")

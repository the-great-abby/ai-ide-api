"""Move memory_vectors table operations from main DB to memorydb (clean base)

Revision ID: 20250611_move_memory_vectors_from_main
Revises: 
Create Date: 2025-06-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20250611_move_memory_vectors_from_main"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create memory_vectors table in its final schema
    op.create_table(
        "memory_vectors",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("namespace", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("meta", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        # Add any other columns needed for final schema
    )
    op.create_index(
        op.f("ix_memory_vectors_project_id"),
        "memory_vectors",
        ["project_id"],
        unique=False,
    )
    # Add any other indexes or constraints as needed

    # Create memory_edges table in its final schema (no index=True in columns)
    op.create_table(
        "memory_edges",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("from_id", sa.String()),
        sa.Column("to_id", sa.String()),
        sa.Column("relation_type", sa.String()),
        sa.Column("meta", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        op.f("ix_memory_edges_from_id"), "memory_edges", ["from_id"], unique=False
    )
    op.create_index(
        op.f("ix_memory_edges_to_id"), "memory_edges", ["to_id"], unique=False
    )
    op.create_index(
        op.f("ix_memory_edges_relation_type"),
        "memory_edges",
        ["relation_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_memory_edges_from_id"), table_name="memory_edges")
    op.drop_index(op.f("ix_memory_edges_to_id"), table_name="memory_edges")
    op.drop_index(op.f("ix_memory_edges_relation_type"), table_name="memory_edges")
    op.drop_table("memory_edges")
    op.drop_index(op.f("ix_memory_vectors_project_id"), table_name="memory_vectors")
    op.drop_table("memory_vectors")

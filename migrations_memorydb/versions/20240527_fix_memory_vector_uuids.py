"""Fix UUID type mismatch in memory_vectors table

Revision ID: 20240527_fix_memory_vector_uuids
Revises: d82e291c4873
Create Date: 2025-05-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "20240527_fix_memory_vector_uuids"
down_revision: Union[str, None] = None  # PATCH: Remove missing dependency for stamping
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    # Update memory_vectors table
    if "memory_vectors" in inspector.get_table_names():
        # Drop foreign key constraints first
        for fk in inspector.get_foreign_keys("memory_vectors"):
            op.drop_constraint(fk["name"], "memory_vectors")

        # Drop indexes that will be recreated
        for idx in inspector.get_indexes("memory_vectors"):
            if idx["name"] in ["ix_memory_vectors_id", "ix_memory_vectors_project_id"]:
                op.drop_index(idx["name"], "memory_vectors")

        # Alter columns to UUID type
        op.alter_column(
            "memory_vectors",
            "id",
            type_=sa.UUID(as_uuid=True),
            postgresql_using="id::uuid",
            existing_type=sa.String(),
            nullable=False,
        )

        op.alter_column(
            "memory_vectors",
            "project_id",
            type_=sa.UUID(as_uuid=True),
            postgresql_using="project_id::uuid",
            existing_type=sa.String(),
            nullable=True,
        )

        # Recreate indexes
        op.create_index("ix_memory_vectors_id", "memory_vectors", ["id"], unique=False)
        op.create_index(
            "ix_memory_vectors_project_id",
            "memory_vectors",
            ["project_id"],
            unique=False,
        )

        # Recreate foreign key constraints
        op.create_foreign_key(
            "fk_memory_vectors_project_id",
            "memory_vectors",
            "projects",
            ["project_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    # Update memory_vectors table
    if "memory_vectors" in inspector.get_table_names():
        # Drop foreign key constraints first
        for fk in inspector.get_foreign_keys("memory_vectors"):
            op.drop_constraint(fk["name"], "memory_vectors")

        # Drop indexes that will be recreated
        for idx in inspector.get_indexes("memory_vectors"):
            if idx["name"] in ["ix_memory_vectors_id", "ix_memory_vectors_project_id"]:
                op.drop_index(idx["name"], "memory_vectors")

        # Alter columns back to String type
        op.alter_column(
            "memory_vectors",
            "id",
            type_=sa.String(),
            postgresql_using="id::text",
            existing_type=sa.UUID(as_uuid=True),
            nullable=False,
        )

        op.alter_column(
            "memory_vectors",
            "project_id",
            type_=sa.String(),
            postgresql_using="project_id::text",
            existing_type=sa.UUID(as_uuid=True),
            nullable=True,
        )

        # Recreate indexes
        op.create_index("ix_memory_vectors_id", "memory_vectors", ["id"], unique=False)
        op.create_index(
            "ix_memory_vectors_project_id",
            "memory_vectors",
            ["project_id"],
            unique=False,
        )

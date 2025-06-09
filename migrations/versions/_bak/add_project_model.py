"""add project model and update related tables

Revision ID: add_project_model
Revises: add_namespace_permissions
Create Date: 2025-05-22 10:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import ARRAY, UUID

# revision identifiers, used by Alembic.
revision: str = "add_project_model"
down_revision: Union[str, None] = "add_namespace_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    try:
        # Create projects table if it doesn't exist
        if "projects" not in inspector.get_table_names():
            op.create_table(
                "projects",
                sa.Column("id", UUID(as_uuid=True), nullable=False),
                sa.Column("name", sa.String(), nullable=False),
                sa.Column("description", sa.String(), nullable=True),
                sa.Column("created_at", sa.DateTime(), nullable=True),
                sa.Column("created_by", sa.String(), nullable=True),
                sa.Column("active", sa.Integer(), nullable=True),
                sa.Column("has_llm_access", sa.Integer(), nullable=True),
                sa.Column("default_namespace", sa.String(), nullable=False),
                sa.Column("namespace_prefix", sa.String(), nullable=False),
                sa.PrimaryKeyConstraint("id"),
            )
    except Exception as e:
        print(f"Error creating projects table: {e}")
        raise

    # Add foreign key constraints if they don't exist
    try:
        if "api_access_tokens" in inspector.get_table_names():
            try:
                op.create_foreign_key(
                    "fk_api_access_tokens_project_id",
                    "api_access_tokens",
                    "projects",
                    ["project_id"],
                    ["id"],
                )
            except Exception as e:
                print(f"Error creating api_access_tokens foreign key: {e}")
    except Exception as e:
        print(f"Error checking api_access_tokens table: {e}")

    try:
        if "namespace_permissions" in inspector.get_table_names():
            try:
                op.create_foreign_key(
                    "fk_namespace_permissions_project_id",
                    "namespace_permissions",
                    "projects",
                    ["project_id"],
                    ["id"],
                )
                op.create_foreign_key(
                    "fk_namespace_permissions_allowed_project_id",
                    "namespace_permissions",
                    "projects",
                    ["allowed_project_id"],
                    ["id"],
                )
            except Exception as e:
                print(f"Error creating namespace_permissions foreign keys: {e}")
    except Exception as e:
        print(f"Error checking namespace_permissions table: {e}")

    try:
        if "memory_vectors" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("memory_vectors")]
            if "project_id" in columns:
                try:
                    op.create_foreign_key(
                        "fk_memory_vectors_project_id",
                        "memory_vectors",
                        "projects",
                        ["project_id"],
                        ["id"],
                    )
                except Exception as e:
                    print(f"Error creating memory_vectors foreign key: {e}")
            else:
                print(
                    "Skipping memory_vectors foreign key: project_id column does not exist."
                )

    except Exception as e:
        print(f"Error checking memory_vectors table: {e}")

    # Add has_llm_access to api_access_tokens if it doesn't exist
    try:
        if "api_access_tokens" in inspector.get_table_names():
            try:
                columns = [
                    c["name"] for c in inspector.get_columns("api_access_tokens")
                ]
                if "has_llm_access" not in columns:
                    op.add_column(
                        "api_access_tokens",
                        sa.Column(
                            "has_llm_access",
                            sa.Integer(),
                            nullable=True,
                            server_default="0",
                        ),
                    )
            except Exception as e:
                print(f"Error adding has_llm_access column: {e}")
    except Exception as e:
        print(f"Error checking api_access_tokens columns: {e}")


def downgrade() -> None:
    # Remove foreign key constraints
    op.drop_constraint(
        "fk_api_access_tokens_project_id", "api_access_tokens", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_namespace_permissions_project_id",
        "namespace_permissions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_namespace_permissions_allowed_project_id",
        "namespace_permissions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_memory_vectors_project_id", "memory_vectors", type_="foreignkey"
    )

    # Remove has_llm_access from api_access_tokens
    op.drop_column("api_access_tokens", "has_llm_access")

    # Drop projects table
    op.drop_table("projects")

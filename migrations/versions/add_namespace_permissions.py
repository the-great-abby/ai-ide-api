"""add namespace permissions and token scoping

Revision ID: add_namespace_permissions
Revises: 99f48ac9b43d
Create Date: 2025-05-21 10:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

# revision identifiers, used by Alembic.
revision: str = "add_namespace_permissions"
down_revision: Union[str, None] = "99f48ac9b43d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # Create namespace_permissions table if it doesn't exist
    if "namespace_permissions" not in inspector.get_table_names():
        op.create_table(
            "namespace_permissions",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("namespace", sa.String(), nullable=False),
            sa.Column("project_id", sa.String(), nullable=False),
            sa.Column("allowed_project_id", sa.String(), nullable=True),
            sa.Column("permission_type", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("created_by", sa.String(), nullable=True),
            sa.Column("active", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_namespace_permissions_namespace",
            "namespace_permissions",
            ["namespace"],
            unique=False,
        )
        op.create_index(
            "ix_namespace_permissions_project_id",
            "namespace_permissions",
            ["project_id"],
            unique=False,
        )
        op.create_index(
            "ix_namespace_permissions_allowed_project_id",
            "namespace_permissions",
            ["allowed_project_id"],
            unique=False,
        )

    # Add new columns to api_access_tokens if they don't exist
    if "api_access_tokens" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("api_access_tokens")]

        if "project_id" not in columns:
            op.add_column(
                "api_access_tokens", sa.Column("project_id", sa.String(), nullable=True)
            )
            op.create_index(
                "ix_api_access_tokens_project_id",
                "api_access_tokens",
                ["project_id"],
                unique=False,
            )

        if "allowed_namespaces" not in columns:
            # Create as JSONB instead of ARRAY(String)
            op.add_column(
                "api_access_tokens",
                sa.Column("allowed_namespaces", JSONB, nullable=True),
            )
        else:
            # If already exists as ARRAY, alter to JSONB
            col_type = [col for col in inspector.get_columns("api_access_tokens") if col["name"] == "allowed_namespaces"][0]["type"]
            if isinstance(col_type, ARRAY):
                op.alter_column(
                    "api_access_tokens",
                    "allowed_namespaces",
                    type_=JSONB,
                    postgresql_using="allowed_namespaces::jsonb",
                )

        if "namespace_permissions" not in columns:
            op.add_column(
                "api_access_tokens",
                sa.Column("namespace_permissions", sa.String(), nullable=True),
            )


def downgrade() -> None:
    # Drop new columns from api_access_tokens
    op.drop_index("ix_api_access_tokens_project_id", table_name="api_access_tokens")
    op.drop_column("api_access_tokens", "namespace_permissions")
    op.drop_column("api_access_tokens", "allowed_namespaces")
    op.drop_column("api_access_tokens", "project_id")

    # Drop namespace_permissions table
    op.drop_index(
        "ix_namespace_permissions_allowed_project_id",
        table_name="namespace_permissions",
    )
    op.drop_index(
        "ix_namespace_permissions_project_id", table_name="namespace_permissions"
    )
    op.drop_index(
        "ix_namespace_permissions_namespace", table_name="namespace_permissions"
    )
    op.drop_table("namespace_permissions")

"""add projects and project_memberships tables

Revision ID: a1b2c3d4e5f6_projmem
Revises: 7754757c36c6
Create Date: 2025-05-18 00:00:00.000000
"""
from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6_projmem"
down_revision: Union[str, None] = "7754757c36c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    # Create projects table if it doesn't exist
    if "projects" not in inspector.get_table_names():
        op.create_table(
            "projects",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("default_namespace", sa.String(), nullable=False),
            sa.Column("default_namespace_description", sa.Text(), nullable=True),
            sa.Column("default_namespace_created_at", sa.DateTime(), nullable=True),
            sa.Column("default_namespace_updated_at", sa.DateTime(), nullable=True),
            sa.Column("default_namespace_deleted_at", sa.DateTime(), nullable=True),
            sa.Column("namespace_prefix", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    # Create project_memberships table if it doesn't exist
    if "project_memberships" not in inspector.get_table_names():
        op.create_table(
            "project_memberships",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("project_id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["project_id"],
                ["projects.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    # Insert default project if it doesn't exist
    if "projects" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("projects")]
        if "id" in columns:
            result = bind.execute(
                text(
                    "SELECT id FROM projects WHERE id = '00000000-0000-0000-0000-000000000000'"
                )
            ).fetchone()
            if not result:
                bind.execute(
                    sa.text(
                        """
                        INSERT INTO projects (id, name, description, created_at, default_namespace, namespace_prefix)
                        VALUES ('00000000-0000-0000-0000-000000000000', 'Default Project', 'For legacy/unscoped data', '2025-05-22T07:53:46.223966', 'default', 'default')
                    """
                    )
                )


def downgrade() -> None:
    op.drop_table("project_memberships")
    op.drop_table("projects")

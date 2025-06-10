"""Convert active columns to BOOLEAN (api_access_tokens, projects, namespace_permissions, teams)

Revision ID: c8846f51d98d
Revises: be05ad5de8f8
Create Date: 2025-06-05 07:12:29.897828

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.exc import NoSuchTableError


# revision identifiers, used by Alembic.
revision: str = 'c8846f51d98d'
down_revision: Union[str, None] = 'be05ad5de8f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    def column_exists(table, column):
        try:
            return column in [col["name"] for col in inspector.get_columns(table)]
        except NoSuchTableError:
            return False

    # 1. api_access_tokens
    if column_exists("api_access_tokens", "active"):
        op.execute("UPDATE api_access_tokens SET active = TRUE WHERE active IS NOT NULL AND active::text != '0';")
        op.execute("UPDATE api_access_tokens SET active = FALSE WHERE active IS NULL OR active::text = '0';")
        op.alter_column(
            'api_access_tokens',
            'active',
            existing_type=sa.Integer(),
            type_=sa.Boolean(),
            postgresql_using='active::boolean',
            existing_nullable=True,
        )

    # 2. projects
    if column_exists("projects", "active"):
        op.execute("UPDATE projects SET active = TRUE WHERE active IS NOT NULL AND active::text != '0';")
        op.execute("UPDATE projects SET active = FALSE WHERE active IS NULL OR active::text = '0';")
        op.alter_column(
            'projects',
            'active',
            existing_type=sa.Integer(),
            type_=sa.Boolean(),
            postgresql_using='active::boolean',
            existing_nullable=True,
        )

    # 3. namespace_permissions
    if column_exists("namespace_permissions", "active"):
        op.execute("UPDATE namespace_permissions SET active = TRUE WHERE active IS NOT NULL AND active::text != '0';")
        op.execute("UPDATE namespace_permissions SET active = FALSE WHERE active IS NULL OR active::text = '0';")
        op.alter_column(
            'namespace_permissions',
            'active',
            existing_type=sa.Integer(),
            type_=sa.Boolean(),
            postgresql_using='active::boolean',
            existing_nullable=True,
        )

    # 4. teams
    if column_exists("teams", "active"):
        op.execute("UPDATE teams SET active = TRUE WHERE active IS NOT NULL AND active::text != '0';")
        op.execute("UPDATE teams SET active = FALSE WHERE active IS NULL OR active::text = '0';")
        op.alter_column(
            'teams',
            'active',
            existing_type=sa.Integer(),
            type_=sa.Boolean(),
            postgresql_using='active::boolean',
            existing_nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Convert 'active' columns from BOOLEAN back to INTEGER in all relevant tables
    # 1. api_access_tokens
    op.execute("UPDATE api_access_tokens SET active = 1 WHERE active = TRUE;")
    op.execute("UPDATE api_access_tokens SET active = 0 WHERE active = FALSE;")
    op.alter_column(
        'api_access_tokens',
        'active',
        existing_type=sa.Boolean(),
        type_=sa.Integer(),
        postgresql_using='active::integer',
        existing_nullable=True,
    )

    # 2. projects
    op.execute("UPDATE projects SET active = 1 WHERE active = TRUE;")
    op.execute("UPDATE projects SET active = 0 WHERE active = FALSE;")
    op.alter_column(
        'projects',
        'active',
        existing_type=sa.Boolean(),
        type_=sa.Integer(),
        postgresql_using='active::integer',
        existing_nullable=True,
    )

    # 3. namespace_permissions
    op.execute("UPDATE namespace_permissions SET active = 1 WHERE active = TRUE;")
    op.execute("UPDATE namespace_permissions SET active = 0 WHERE active = FALSE;")
    op.alter_column(
        'namespace_permissions',
        'active',
        existing_type=sa.Boolean(),
        type_=sa.Integer(),
        postgresql_using='active::integer',
        existing_nullable=True,
    )

    # 4. teams
    op.execute("UPDATE teams SET active = 1 WHERE active = TRUE;")
    op.execute("UPDATE teams SET active = 0 WHERE active = FALSE;")
    op.alter_column(
        'teams',
        'active',
        existing_type=sa.Boolean(),
        type_=sa.Integer(),
        postgresql_using='active::integer',
        existing_nullable=True,
    )

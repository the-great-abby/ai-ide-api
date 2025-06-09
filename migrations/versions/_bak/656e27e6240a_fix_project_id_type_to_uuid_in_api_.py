"""Fix project_id type to UUID in api_access_tokens and namespace_permissions

Revision ID: 656e27e6240a
Revises: c8846f51d98d
Create Date: 2025-06-05 07:59:46.346519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '656e27e6240a'
down_revision: Union[str, None] = 'c8846f51d98d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Convert api_access_tokens.project_id from VARCHAR to UUID
    op.alter_column(
        'api_access_tokens',
        'project_id',
        existing_type=sa.String(),
        type_=sa.UUID(),
        existing_nullable=True,
        postgresql_using='project_id::uuid',
    )
    # Convert namespace_permissions.project_id from VARCHAR to UUID if needed
    with op.get_bind() as conn:
        result = conn.execute(
            sa.text("""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'namespace_permissions' AND column_name = 'project_id'
            """))
        data_type = result.scalar()
        if data_type == 'character varying':
            op.alter_column(
                'namespace_permissions',
                'project_id',
                existing_type=sa.String(),
                type_=sa.UUID(),
                existing_nullable=False,
                postgresql_using='project_id::uuid',
            )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert api_access_tokens.project_id from UUID to VARCHAR
    op.alter_column(
        'api_access_tokens',
        'project_id',
        existing_type=sa.UUID(),
        type_=sa.String(),
        existing_nullable=True,
        postgresql_using='project_id::varchar',
    )
    # Revert namespace_permissions.project_id from UUID to VARCHAR if needed
    with op.get_bind() as conn:
        result = conn.execute(
            sa.text("""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'namespace_permissions' AND column_name = 'project_id'
            """))
        data_type = result.scalar()
        if data_type == 'uuid':
            op.alter_column(
                'namespace_permissions',
                'project_id',
                existing_type=sa.UUID(),
                type_=sa.String(),
                existing_nullable=False,
                postgresql_using='project_id::varchar',
            )

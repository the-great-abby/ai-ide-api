"""add superseded_by column to rules table

Revision ID: 310ce55660a8
Revises: aba36a03157c
Create Date: 2025-06-13 11:02:25.441286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '310ce55660a8'
down_revision: Union[str, None] = 'aba36a03157c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Only alter project column types if needed
    op.alter_column('rules', 'project',
        existing_type=sa.VARCHAR(),
        type_=sa.UUID(),
        existing_nullable=True,
        postgresql_using="project::uuid"
    )
    op.alter_column('rule_versions', 'project',
        existing_type=sa.VARCHAR(),
        type_=sa.UUID(),
        existing_nullable=True,
        postgresql_using="project::uuid"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('rule_versions', 'project',
        existing_type=sa.UUID(),
        type_=sa.VARCHAR(),
        existing_nullable=True,
        postgresql_using="project::varchar"
    )
    op.alter_column('rules', 'project',
        existing_type=sa.UUID(),
        type_=sa.VARCHAR(),
        existing_nullable=True,
        postgresql_using="project::varchar"
    )

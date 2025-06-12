"""add superseded_by to rules

Revision ID: cc603753feaf
Revises: 23b59ec9a17b
Create Date: 2025-06-12 12:30:43.499701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cc603753feaf'
down_revision: Union[str, None] = '23b59ec9a17b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('rules', sa.Column('superseded_by', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('rules', 'superseded_by')

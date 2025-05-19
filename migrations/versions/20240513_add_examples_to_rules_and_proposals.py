"""add examples column to rules and proposals

Revision ID: 20240513_add_examples
Revises: 326e17ceb7de
Create Date: 2025-05-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20240513_add_examples"
down_revision: Union[str, None] = "326e17ceb7de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("rules", sa.Column("examples", sa.Text(), nullable=True))
    op.add_column("proposals", sa.Column("examples", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("rules", "examples")
    op.drop_column("proposals", "examples")

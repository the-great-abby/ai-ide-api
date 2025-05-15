"""empty message

Revision ID: 98d34407c6f1
Revises: add_user_story_to_enhancements, c77f4c2517b0
Create Date: 2025-05-15 12:04:26.505969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98d34407c6f1'
down_revision: Union[str, None] = ('add_user_story_to_enhancements', 'c77f4c2517b0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("rules", sa.Column("user_story", sa.Text(), nullable=True))
    op.add_column("proposals", sa.Column("user_story", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("rules", "user_story")
    op.drop_column("proposals", "user_story")

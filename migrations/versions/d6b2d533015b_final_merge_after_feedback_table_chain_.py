"""Final merge after feedback table chain fix

Revision ID: d6b2d533015b
Revises: merge_f281313beb28_and_fd273470995c, merge_final_final_final_all_heads
Create Date: 2025-06-06 20:45:12.256540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6b2d533015b'
down_revision: Union[str, None] = ('merge_f281313beb28_and_fd273470995c', 'merge_final_final_final_all_heads')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

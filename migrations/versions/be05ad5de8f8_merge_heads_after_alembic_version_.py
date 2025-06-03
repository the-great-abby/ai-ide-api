"""merge heads after alembic_version length patch

Revision ID: be05ad5de8f8
Revises: 20240603_alter_alembic_version_num_length, 9762530cfa02
Create Date: 2025-06-03 13:12:36.868937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be05ad5de8f8'
down_revision: Union[str, None] = ('20240603_alter_alembic_version_num_length', '9762530cfa02')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

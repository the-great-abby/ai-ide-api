"""auto-merge heads

Revision ID: bf9e065008bf
Revises: 20240513_add_examples
Create Date: 2025-05-13 02:46:07.894378

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bf9e065008bf"
down_revision: Union[str, None] = "20240513_add_examples"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

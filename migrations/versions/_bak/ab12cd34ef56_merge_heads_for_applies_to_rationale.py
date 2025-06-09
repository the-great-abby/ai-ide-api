"""
Merge heads for applies_to_rationale addition

Revision ID: ab12cd34ef56
Revises: cd49c47dfc87
Create Date: 2024-06-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ab12cd34ef56"
down_revision: Union[str, None] = "cd49c47dfc87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

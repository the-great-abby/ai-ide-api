"""merge namespace_prefix and previous heads

Revision ID: f281313beb28
Revises: 20240613_add_namespace_prefix_to_projects, fd273470995c
Create Date: 2025-06-06 12:11:05.957227

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f281313beb28'
down_revision: Union[str, None] = '2bd1e2ecd6dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""Merge main DB heads

Revision ID: 9762530cfa02
Revises: 20240603_convert_allowed_namespaces_to_jsonb, d82e291c4873
Create Date: 2025-06-03 12:33:14.388408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9762530cfa02'
down_revision: Union[str, None] = ('20240603_convert_allowed_namespaces_to_jsonb', 'd82e291c4873')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

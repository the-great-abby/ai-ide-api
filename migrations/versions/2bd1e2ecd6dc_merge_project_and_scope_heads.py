"""merge_project_and_scope_heads

Revision ID: 2bd1e2ecd6dc
Revises: 8a41aeb0a5fb
Create Date: 2025-05-22 06:22:14.511785

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2bd1e2ecd6dc"
down_revision: Union[str, None] = "8a41aeb0a5fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""
Linearize all branches after UUID migration

Revision ID: linearize_after_uuid
Revises: c8b957ff43ca
Create Date: 2024-06-07
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'linearize_after_uuid'
down_revision: Union[str, None] = 'c8b957ff43ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass 
"""
Final merge: merge_final_linear_all_heads

Revision ID: merge_really_final_all_heads
Revises: merge_final_linear_all_heads
Create Date: 2024-06-07
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'merge_really_final_all_heads'
down_revision: Union[str, None] = 'merge_final_linear_all_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass 
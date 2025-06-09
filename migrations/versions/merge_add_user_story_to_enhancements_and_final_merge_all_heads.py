"""
Merge heads add_user_story_to_enhancements and final_merge_all_heads

Revision ID: merge_add_user_story_to_enhancements_and_final_merge_all_heads
Revises: final_merge_all_heads
Create Date: 2024-06-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'merge_add_user_story_to_enhancements_and_final_merge_all_heads'
down_revision: Union[str, None] = 'final_merge_all_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass 
"""
Merge all heads as of 2024-06-14 to linearize migration history after consolidation and repair.

Revision ID: merge_heads_20240614
Revises: 20240614_consolidated_schema, 656e27e6240a, d147dc420531, merge_add_user_story_to_enhancements_and_final_merge_all_heads
Create Date: 2024-06-14

This migration merges all outstanding heads after major migration cleanup and consolidation.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'merge_heads_20240614'
down_revision: Union[str, Sequence[str], None] = (
    '20240614_consolidated_schema',
    '656e27e6240a',
    'd147dc420531',
    'merge_add_user_story_to_enhancements_and_final_merge_all_heads',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """No-op merge migration to linearize heads after consolidation."""
    pass

def downgrade() -> None:
    """No-op downgrade for merge migration."""
    pass 
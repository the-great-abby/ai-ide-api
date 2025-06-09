"""Merge minimal and main heads

Revision ID: 0007_merge_minimal_and_main_heads
Revises: 0006_minimal_test_table, d7d3d0ca65f9
Create Date: 2024-06-05
"""
from typing import Sequence, Union

revision: str = "0007_merge_minimal_and_main_heads"
down_revision: Union[str, tuple[str, ...]] = ("0006_minimal_test_table", "d7d3d0ca65f9")
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass 
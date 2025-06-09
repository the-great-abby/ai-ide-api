"""Debug migration: create debug_side_effect table, insert a row, and log to file

Revision ID: 0005_debug_side_effect
Revises: 0004_create_rules
Create Date: 2024-06-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import os

revision: str = "0005_debug_side_effect"
down_revision: Union[str, None] = "0004_create_rules"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create a debug table
    op.create_table(
        "debug_side_effect",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("message", sa.String(255), nullable=False),
    )
    # Insert a row
    op.execute("INSERT INTO debug_side_effect (message) VALUES ('debug migration ran')")
    # Log to a file (if possible)
    try:
        with open("/tmp/alembic_debug.log", "a") as f:
            f.write("Debug migration ran!\n")
    except Exception as e:
        pass

def downgrade() -> None:
    op.drop_table("debug_side_effect") 
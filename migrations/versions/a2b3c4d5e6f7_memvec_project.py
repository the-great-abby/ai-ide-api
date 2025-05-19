"""add project_id to memory_vectors

Revision ID: a2b3c4d5e6f7_memvec_project
Revises: a1b2c3d4e5f6_projmem
Create Date: 2025-05-18 01:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7_memvec_project'
down_revision: Union[str, None] = 'a1b2c3d4e5f6_projmem'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add project_id column (nullable for now)
    op.add_column('memory_vectors', sa.Column('project_id', sa.String(), nullable=True))
    # Set all existing rows to the default project
    op.execute("""
        UPDATE memory_vectors SET project_id = '00000000-0000-0000-0000-000000000000' WHERE project_id IS NULL;
    """)

def downgrade() -> None:
    op.drop_column('memory_vectors', 'project_id') 
"""Remove confidence column from memory_vectors

Revision ID: 20250617_remove_confidence_from_memory_vectors
Revises: 20250611_move_memory_vectors_from_main
Create Date: 2025-06-17

"""
from alembic import op
import sqlalchemy as sa

revision = '20250617_remove_confidence_from_memory_vectors'
down_revision = '20250611_move_memory_vectors_from_main'
branch_labels = None
depends_on = None

def upgrade():
    op.drop_column('memory_vectors', 'confidence')

def downgrade():
    op.add_column('memory_vectors', sa.Column('confidence', sa.Float(), nullable=True)) 
"""
Add confidence column to memory_vectors

Arrr matey! This be the migration that brings confidence to yer memories!

Revision ID: 20240613_add_confidence_to_memoryvector
Revises: 20240603_alter_alembic_version_num_length_memorydb
Create Date: 2024-06-13
"""

revision = '20240613_add_confidence_to_memoryvector'
down_revision = '20240603_alter_alembic_version_num_length_memorydb'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('memory_vectors', sa.Column('confidence', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('memory_vectors', 'confidence') 
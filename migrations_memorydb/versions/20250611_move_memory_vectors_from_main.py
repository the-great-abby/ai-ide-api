"""Move memory_vectors table operations from main DB to memorydb

Revision ID: 20250611_move_memory_vectors_from_main
Revises: 
Create Date: 2025-06-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20250611_move_memory_vectors_from_main"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # --- memory_vectors operations moved from main migration ---
    op.add_column('memory_vectors', sa.Column('project_id', sa.String(), nullable=False))
    op.add_column('memory_vectors', sa.Column('confidence', sa.Float(), nullable=True))
    op.alter_column('memory_vectors', 'namespace',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('memory_vectors', 'content',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=False)
    op.alter_column('memory_vectors', 'meta',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=True)
    op.drop_index(op.f('ix_memory_vectors_reference_id'), table_name='memory_vectors')
    op.create_index(op.f('ix_memory_vectors_project_id'), 'memory_vectors', ['project_id'], unique=False)
    op.create_foreign_key(None, 'memory_vectors', 'projects', ['project_id'], ['id'])
    op.drop_column('memory_vectors', 'reference_id')

def downgrade() -> None:
    op.add_column('memory_vectors', sa.Column('reference_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'memory_vectors', type_='foreignkey')
    op.drop_index(op.f('ix_memory_vectors_project_id'), table_name='memory_vectors')
    op.create_index(op.f('ix_memory_vectors_reference_id'), 'memory_vectors', ['reference_id'], unique=False)
    op.alter_column('memory_vectors', 'meta',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=True)
    op.alter_column('memory_vectors', 'content',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('memory_vectors', 'namespace',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.drop_column('memory_vectors', 'confidence')
    op.drop_column('memory_vectors', 'project_id') 
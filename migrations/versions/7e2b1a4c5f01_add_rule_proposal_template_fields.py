"""
Add reason_for_change, references, and current_rule columns to proposals table

Revision ID: 7e2b1a4c5f01
Revises: e1f2a3b4c5d6
Create Date: 2024-06-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7e2b1a4c5f01'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('proposals', sa.Column('reason_for_change', sa.Text(), nullable=True))
    op.add_column('proposals', sa.Column('references', sa.Text(), nullable=True))
    op.add_column('proposals', sa.Column('current_rule', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('proposals', 'reason_for_change')
    op.drop_column('proposals', 'references')
    op.drop_column('proposals', 'current_rule') 
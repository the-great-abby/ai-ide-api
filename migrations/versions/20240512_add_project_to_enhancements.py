"""
Add project column to enhancements table

Revision ID: a1b2c3d4e5f6
Revises: edeeb4090649
Create Date: 2025-05-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'edeeb4090649'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('enhancements', sa.Column('project', sa.String(length=255), nullable=True))

def downgrade():
    op.drop_column('enhancements', 'project') 
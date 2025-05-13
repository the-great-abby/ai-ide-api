"""
Add project to enhancements

Revision ID: f7e8d9c0b1a2
Revises: edeeb4090649
Create Date: 2025-05-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f7e8d9c0b1a2'
down_revision = 'edeeb4090649'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('enhancements', sa.Column('project', sa.String(length=255), nullable=True))

def downgrade():
    op.drop_column('enhancements', 'project') 
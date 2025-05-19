"""add project_onboarding_progress table for onboarding tracking

Revision ID: b2e1c3d4f5a6
Revises: a0788ee96bea
Create Date: 2024-05-20
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'b2e1c3d4f5a6'
down_revision = 'a0788ee96bea'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # If the table does not exist, create it (as before)
    if not op.get_bind().dialect.has_table(op.get_bind(), 'project_onboarding_progress'):
        op.create_table(
            'project_onboarding_progress',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('project_id', sa.String(), nullable=False),
            sa.Column('path', sa.String(), nullable=False),
            sa.Column('step', sa.String(), nullable=False),
            sa.Column('completed', sa.Boolean(), default=False),
            sa.Column('timestamp', sa.DateTime(), default=datetime.utcnow),
            sa.Column('details', sa.JSON(), nullable=True),
        )
    else:
        # If the table exists, add the 'path' column if not present
        with op.batch_alter_table('project_onboarding_progress') as batch_op:
            batch_op.add_column(sa.Column('path', sa.String(), nullable=False, server_default='default'))
            batch_op.alter_column('path', server_default=None)

def downgrade() -> None:
    # Remove the 'path' column if it exists
    with op.batch_alter_table('project_onboarding_progress') as batch_op:
        batch_op.drop_column('path')
    # Optionally drop the table (if you want to fully revert)
    # op.drop_table('project_onboarding_progress') 
"""add project_onboarding_progress table for onboarding tracking

Revision ID: b2e1c3d4f5a6
Revises: a0788ee96bea
Create Date: 2024-05-20
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'b2e1c3d4f5a6'
down_revision = 'a0788ee96bea'
branch_labels = None
depends_on = None

def upgrade() -> None:
    print('--- MIGRATION: Starting creation of project_onboarding_progress table ---')
    try:
        bind = op.get_bind()
        inspector = inspect(bind)
        
        # Only create the table if it doesn't exist
        if 'project_onboarding_progress' not in inspector.get_table_names():
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
            print('--- MIGRATION: Successfully created project_onboarding_progress table ---')
        else:
            print('--- MIGRATION: project_onboarding_progress table already exists ---')
    except Exception as e:
        print(f'--- MIGRATION ERROR: {e} ---')
        raise

def downgrade() -> None:
    # Remove the 'path' column if it exists
    with op.batch_alter_table('project_onboarding_progress') as batch_op:
        batch_op.drop_column('path')
    # Optionally drop the table (if you want to fully revert)
    # op.drop_table('project_onboarding_progress') 
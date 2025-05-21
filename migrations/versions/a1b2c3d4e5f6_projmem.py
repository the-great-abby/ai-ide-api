"""add projects and project_memberships tables

Revision ID: a1b2c3d4e5f6_projmem
Revises: 7754757c36c6
Create Date: 2025-05-18 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6_projmem'
down_revision: Union[str, None] = '7754757c36c6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    # Create projects table if it doesn't exist
    if 'projects' not in inspector.get_table_names():
        op.create_table(
            'projects',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        )
    # Create project_memberships table if it doesn't exist
    if 'project_memberships' not in inspector.get_table_names():
        op.create_table(
            'project_memberships',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('project_id', sa.String(), nullable=False),
            sa.Column('role', sa.String(), default='admin'),
        )
    # Insert default project for legacy/unscoped data if it doesn't exist
    default_project_id = '00000000-0000-0000-0000-000000000000'
    if 'projects' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('projects')]
        if 'id' in columns:
            result = bind.execute(text(f"SELECT id FROM projects WHERE id = '{default_project_id}'")).fetchone()
            if not result:
                bind.execute(
                    text(f"""
                    INSERT INTO projects (id, name, description, created_at)
                    VALUES ('{default_project_id}', 'Default Project', 'For legacy/unscoped data', '{datetime.utcnow().isoformat()}')
                    """)
                )

def downgrade() -> None:
    op.drop_table('project_memberships')
    op.drop_table('projects') 
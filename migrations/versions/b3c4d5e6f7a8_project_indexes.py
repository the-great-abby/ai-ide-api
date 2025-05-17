"""add project_id to api_access_tokens and add project_id indexes

Revision ID: b3c4d5e6f7a8_project_indexes
Revises: a2b3c4d5e6f7_memvec_project
Create Date: 2025-05-18 01:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8_project_indexes'
down_revision: Union[str, None] = 'a2b3c4d5e6f7_memvec_project'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add project_id to api_access_tokens
    op.add_column('api_access_tokens', sa.Column('project_id', sa.String(), nullable=True))
    op.execute("""
        UPDATE api_access_tokens SET project_id = '00000000-0000-0000-0000-000000000000' WHERE project_id IS NULL;
    """)
    op.create_index('ix_api_access_tokens_project_id', 'api_access_tokens', ['project_id'], unique=False)
    # Add indexes to all relevant tables using IF NOT EXISTS for safety
    op.create_index('ix_memory_vectors_project_id', 'memory_vectors', ['project_id'], unique=False)
    op.execute("CREATE INDEX IF NOT EXISTS ix_rules_project ON rules (project);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_proposals_project ON proposals (project);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enhancements_project ON enhancements (project);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedback_project ON feedback (project);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_rule_versions_project ON rule_versions (project);")

def downgrade() -> None:
    op.drop_index('ix_api_access_tokens_project_id', table_name='api_access_tokens')
    op.drop_column('api_access_tokens', 'project_id')
    op.drop_index('ix_memory_vectors_project_id', table_name='memory_vectors')
    op.drop_index('ix_rules_project', table_name='rules')
    op.drop_index('ix_proposals_project', table_name='proposals')
    op.drop_index('ix_enhancements_project', table_name='enhancements')
    op.drop_index('ix_feedback_project', table_name='feedback')
    op.drop_index('ix_rule_versions_project', table_name='rule_versions') 
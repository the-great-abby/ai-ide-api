"""add_scope_fields_to_rules

Revision ID: bc451ac85c74
Revises: 0e2e70527d19
Create Date: 2025-05-21 05:04:44.284973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'bc451ac85c74'
down_revision: Union[str, None] = '0e2e70527d19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Get database inspector
    inspector = inspect(op.get_bind())
    
    # Helper function to check if column exists
    def column_exists(table_name: str, column_name: str) -> bool:
        return column_name in [col['name'] for col in inspector.get_columns(table_name)]
    
    # Add columns to proposals if they don't exist
    if not column_exists('proposals', 'scope_level'):
        op.add_column('proposals', sa.Column('scope_level', sa.String(), nullable=False, server_default='global'))
        op.create_index(op.f('ix_proposals_scope_level'), 'proposals', ['scope_level'], unique=False)
    
    if not column_exists('proposals', 'scope_id'):
        op.add_column('proposals', sa.Column('scope_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_proposals_scope_id'), 'proposals', ['scope_id'], unique=False)
    
    if not column_exists('proposals', 'parent_rule_id'):
        op.add_column('proposals', sa.Column('parent_rule_id', sa.String(), nullable=True))
    
    # Add columns to rule_versions if they don't exist
    if not column_exists('rule_versions', 'scope_level'):
        op.add_column('rule_versions', sa.Column('scope_level', sa.String(), nullable=False, server_default='global'))
        op.create_index(op.f('ix_rule_versions_scope_level'), 'rule_versions', ['scope_level'], unique=False)
    
    if not column_exists('rule_versions', 'scope_id'):
        op.add_column('rule_versions', sa.Column('scope_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_rule_versions_scope_id'), 'rule_versions', ['scope_id'], unique=False)
    
    if not column_exists('rule_versions', 'parent_rule_id'):
        op.add_column('rule_versions', sa.Column('parent_rule_id', sa.String(), nullable=True))
    
    # Add columns to rules if they don't exist
    if not column_exists('rules', 'scope_level'):
        op.add_column('rules', sa.Column('scope_level', sa.String(), nullable=False, server_default='global'))
        op.create_index(op.f('ix_rules_scope_level'), 'rules', ['scope_level'], unique=False)
    
    if not column_exists('rules', 'scope_id'):
        op.add_column('rules', sa.Column('scope_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_rules_scope_id'), 'rules', ['scope_id'], unique=False)
    
    if not column_exists('rules', 'parent_rule_id'):
        op.add_column('rules', sa.Column('parent_rule_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Get database inspector
    inspector = inspect(op.get_bind())
    
    # Helper function to check if column exists
    def column_exists(table_name: str, column_name: str) -> bool:
        return column_name in [col['name'] for col in inspector.get_columns(table_name)]
    
    # Drop columns from rules if they exist
    if column_exists('rules', 'scope_level'):
        op.drop_index(op.f('ix_rules_scope_level'), table_name='rules')
        op.drop_column('rules', 'scope_level')
    
    if column_exists('rules', 'scope_id'):
        op.drop_index(op.f('ix_rules_scope_id'), table_name='rules')
        op.drop_column('rules', 'scope_id')
    
    if column_exists('rules', 'parent_rule_id'):
        op.drop_column('rules', 'parent_rule_id')
    
    # Drop columns from rule_versions if they exist
    if column_exists('rule_versions', 'scope_level'):
        op.drop_index(op.f('ix_rule_versions_scope_level'), table_name='rule_versions')
        op.drop_column('rule_versions', 'scope_level')
    
    if column_exists('rule_versions', 'scope_id'):
        op.drop_index(op.f('ix_rule_versions_scope_id'), table_name='rule_versions')
        op.drop_column('rule_versions', 'scope_id')
    
    if column_exists('rule_versions', 'parent_rule_id'):
        op.drop_column('rule_versions', 'parent_rule_id')
    
    # Drop columns from proposals if they exist
    if column_exists('proposals', 'scope_level'):
        op.drop_index(op.f('ix_proposals_scope_level'), table_name='proposals')
        op.drop_column('proposals', 'scope_level')
    
    if column_exists('proposals', 'scope_id'):
        op.drop_index(op.f('ix_proposals_scope_id'), table_name='proposals')
        op.drop_column('proposals', 'scope_id')
    
    if column_exists('proposals', 'parent_rule_id'):
        op.drop_column('proposals', 'parent_rule_id')

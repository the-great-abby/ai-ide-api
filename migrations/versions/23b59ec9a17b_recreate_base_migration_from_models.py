"""Recreate base migration from models (clean, merged)

Revision ID: 23b59ec9a17b
Revises: 
Create Date: 2025-06-11 12:31:42.949368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '23b59ec9a17b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # --- Core tables (no FKs) ---
    op.create_table('projects',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), default=True),
        sa.Column('has_llm_access', sa.Integer(), default=0),
        sa.Column('default_namespace', sa.String(), nullable=False),
        sa.Column('namespace_prefix', sa.String(), nullable=False),
    )
    op.create_table('teams',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
    )
    op.create_table('use_cases',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('example_workflow', sa.JSON(), nullable=False),
        sa.Column('tags', sa.String(length=255), nullable=True),
        sa.Column('categories', sa.String(length=255), nullable=True),
        sa.Column('submitted_by', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=True),
    )
    op.create_index(op.f('ix_use_cases_id'), 'use_cases', ['id'], unique=False)
    # --- Tables with FKs to projects ---
    op.create_table('project_memberships',
        sa.Column('id', sa.String(), primary_key=True),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('project_id', sa.String(), nullable=False),
    sa.Column('role', sa.String(), nullable=True),
    )
    op.create_table('namespace_permissions',
        sa.Column('id', sa.String(), primary_key=True),
    sa.Column('namespace', sa.String(), nullable=False),
    sa.Column('project_id', sa.String(), nullable=False),
    sa.Column('allowed_project_id', sa.String(), nullable=True),
    sa.Column('permission_type', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['allowed_project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
    )
    op.create_index(op.f('ix_namespace_permissions_allowed_project_id'), 'namespace_permissions', ['allowed_project_id'], unique=False)
    op.create_index(op.f('ix_namespace_permissions_namespace'), 'namespace_permissions', ['namespace'], unique=False)
    op.create_index(op.f('ix_namespace_permissions_project_id'), 'namespace_permissions', ['project_id'], unique=False)
    op.create_table('api_access_tokens',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('token', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('allowed_namespaces', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('namespace_permissions', sa.String(), nullable=True),
        sa.Column('has_llm_access', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
    )
    op.create_index(op.f('ix_api_access_tokens_project_id'), 'api_access_tokens', ['project_id'], unique=False)
    op.create_index(op.f('ix_api_access_tokens_token'), 'api_access_tokens', ['token'], unique=True)
    # --- Other core tables ---
    op.create_table('api_error_logs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('path', sa.String(), nullable=True),
        sa.Column('method', sa.String(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
    )
    op.create_table('bug_reports',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reporter', sa.String(), nullable=True),
        sa.Column('page', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('user_story', sa.String(), nullable=True),
    )
    op.create_index(op.f('ix_bug_reports_id'), 'bug_reports', ['id'], unique=False)
    op.create_table('enhancements',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('suggested_by', sa.String(), nullable=True),
        sa.Column('page', sa.String(), nullable=True),
        sa.Column('tags', sa.String(), nullable=True),
        sa.Column('categories', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('proposal_id', sa.String(), nullable=True),
        sa.Column('project', sa.String(), nullable=True),
        sa.Column('examples', sa.Text(), nullable=True),
        sa.Column('applies_to', sa.String(), nullable=True),
        sa.Column('applies_to_rationale', sa.Text(), nullable=True),
        sa.Column('user_story', sa.Text(), nullable=True),
        sa.Column('diff', sa.Text(), nullable=True),
        sa.Column('scope_level', sa.String(), nullable=False),
        sa.Column('scope_id', sa.String(), nullable=True),
        sa.Column('parent_rule_id', sa.String(), nullable=True),
    )
    op.create_index(op.f('ix_enhancements_id'), 'enhancements', ['id'], unique=False)
    op.create_index(op.f('ix_enhancements_project'), 'enhancements', ['project'], unique=False)
    op.create_index(op.f('ix_enhancements_scope_id'), 'enhancements', ['scope_id'], unique=False)
    op.create_index(op.f('ix_enhancements_scope_level'), 'enhancements', ['scope_level'], unique=False)
    op.create_table('feedback',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('rule_id', sa.String(), nullable=True),
        sa.Column('project', sa.String(), nullable=True),
        sa.Column('feedback_type', sa.String(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('submitted_by', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)
    op.create_index(op.f('ix_feedback_project'), 'feedback', ['project'], unique=False)
    op.create_index(op.f('ix_feedback_rule_id'), 'feedback', ['rule_id'], unique=False)
    op.create_index(op.f('ix_feedback_submitted_by'), 'feedback', ['submitted_by'], unique=False)
    op.create_table('project_onboarding_progress',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('step', sa.String(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.UniqueConstraint('project_id', 'path', 'step', 'version', name='uix_project_path_step_version'),
    )
    op.create_table('rule_proposal_feedback',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('rule_proposal_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('feedback_type', sa.String(), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_rule_proposal_feedback_id'), 'rule_proposal_feedback', ['id'], unique=False)
    op.create_table('rule_proposals',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('submitted_by', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
    )
    op.create_index(op.f('ix_rule_proposals_id'), 'rule_proposals', ['id'], unique=False)
    op.create_table('rule_versions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('rule_id', sa.String(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('rule_type', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('diff', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('submitted_by', sa.String(), nullable=True),
        sa.Column('added_by', sa.String(), nullable=True),
        sa.Column('project', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('categories', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('examples', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('applies_to', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('applies_to_rationale', sa.Text(), nullable=True),
        sa.Column('user_story', sa.Text(), nullable=True),
        sa.Column('scope_level', sa.String(), nullable=False),
        sa.Column('scope_id', sa.String(), nullable=True),
        sa.Column('parent_rule_id', sa.String(), nullable=True),
    )
    op.create_index(op.f('ix_rule_versions_id'), 'rule_versions', ['id'], unique=False)
    op.create_index(op.f('ix_rule_versions_rule_id'), 'rule_versions', ['rule_id'], unique=False)
    op.create_index(op.f('ix_rule_versions_scope_id'), 'rule_versions', ['scope_id'], unique=False)
    op.create_index(op.f('ix_rule_versions_scope_level'), 'rule_versions', ['scope_level'], unique=False)
    op.create_table('rules',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('rule_type', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('diff', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('submitted_by', sa.String(), nullable=True),
        sa.Column('added_by', sa.String(), nullable=True),
        sa.Column('project', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('categories', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('examples', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('applies_to', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('applies_to_rationale', sa.Text(), nullable=True),
        sa.Column('user_story', sa.Text(), nullable=True),
        sa.Column('scope_level', sa.String(), nullable=False),
        sa.Column('scope_id', sa.String(), nullable=True),
        sa.Column('parent_rule_id', sa.String(), nullable=True),
        sa.Column('superseded_by', sa.String(), nullable=True),
    )
    op.create_index(op.f('ix_rules_added_by'), 'rules', ['added_by'], unique=False)
    op.create_index(op.f('ix_rules_id'), 'rules', ['id'], unique=False)
    op.create_index(op.f('ix_rules_project'), 'rules', ['project'], unique=False)
    op.create_index(op.f('ix_rules_rule_type'), 'rules', ['rule_type'], unique=False)
    op.create_index(op.f('ix_rules_scope_id'), 'rules', ['scope_id'], unique=False)
    op.create_index(op.f('ix_rules_scope_level'), 'rules', ['scope_level'], unique=False)
    op.create_index(op.f('ix_rules_submitted_by'), 'rules', ['submitted_by'], unique=False)
    # --- End of schema ---

def downgrade() -> None:
    # (Optional: implement drop logic if needed)
    pass

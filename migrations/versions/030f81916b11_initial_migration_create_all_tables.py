"""initial migration: create all tables

Revision ID: 030f81916b11
Revises: 
Create Date: 2025-05-12 00:30:01.394054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '030f81916b11'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Explicit enum creation removed; let table definitions handle it
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'feedback' not in inspector.get_table_names():
        op.create_table('feedback',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('rule_id', sa.String(), nullable=True),
            sa.Column('project', sa.String(), nullable=True),
            sa.Column('feedback_type', sa.String(), nullable=True),
            sa.Column('comment', sa.Text(), nullable=True),
            sa.Column('submitted_by', sa.String(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)
        op.create_index(op.f('ix_feedback_project'), 'feedback', ['project'], unique=False)
        op.create_index(op.f('ix_feedback_rule_id'), 'feedback', ['rule_id'], unique=False)
        op.create_index(op.f('ix_feedback_submitted_by'), 'feedback', ['submitted_by'], unique=False)
    if 'proposals' not in inspector.get_table_names():
        op.create_table('proposals',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('rule_type', sa.String(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('diff', sa.Text(), nullable=True),
            sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'reverted_to_enhancement', name='statusenum'), nullable=True),
            sa.Column('submitted_by', sa.String(), nullable=True),
            sa.Column('project', sa.String(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=True),
            sa.Column('categories', sa.String(), nullable=True),
            sa.Column('tags', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_proposals_id'), 'proposals', ['id'], unique=False)
        op.create_index(op.f('ix_proposals_project'), 'proposals', ['project'], unique=False)
        op.create_index(op.f('ix_proposals_rule_type'), 'proposals', ['rule_type'], unique=False)
        op.create_index(op.f('ix_proposals_submitted_by'), 'proposals', ['submitted_by'], unique=False)
    if 'rule_versions' not in inspector.get_table_names():
        op.create_table('rule_versions',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('rule_id', sa.String(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=True),
            sa.Column('rule_type', sa.String(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('diff', sa.Text(), nullable=True),
            sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='statusenum'), nullable=True),
            sa.Column('submitted_by', sa.String(), nullable=True),
            sa.Column('added_by', sa.String(), nullable=True),
            sa.Column('project', sa.String(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('categories', sa.String(), nullable=True),
            sa.Column('tags', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_rule_versions_id'), 'rule_versions', ['id'], unique=False)
        op.create_index(op.f('ix_rule_versions_rule_id'), 'rule_versions', ['rule_id'], unique=False)
    if 'rules' not in inspector.get_table_names():
        op.create_table('rules',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('rule_type', sa.String(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('diff', sa.Text(), nullable=True),
            sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='statusenum'), nullable=True),
            sa.Column('submitted_by', sa.String(), nullable=True),
            sa.Column('added_by', sa.String(), nullable=True),
            sa.Column('project', sa.String(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=True),
            sa.Column('categories', sa.String(), nullable=True),
            sa.Column('tags', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_rules_added_by'), 'rules', ['added_by'], unique=False)
        op.create_index(op.f('ix_rules_id'), 'rules', ['id'], unique=False)
        op.create_index(op.f('ix_rules_project'), 'rules', ['project'], unique=False)
        op.create_index(op.f('ix_rules_rule_type'), 'rules', ['rule_type'], unique=False)
        op.create_index(op.f('ix_rules_submitted_by'), 'rules', ['submitted_by'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_rules_submitted_by'), table_name='rules')
    op.drop_index(op.f('ix_rules_rule_type'), table_name='rules')
    op.drop_index(op.f('ix_rules_project'), table_name='rules')
    op.drop_index(op.f('ix_rules_id'), table_name='rules')
    op.drop_index(op.f('ix_rules_added_by'), table_name='rules')
    op.drop_table('rules')
    op.drop_index(op.f('ix_rule_versions_rule_id'), table_name='rule_versions')
    op.drop_index(op.f('ix_rule_versions_id'), table_name='rule_versions')
    op.drop_table('rule_versions')
    op.drop_index(op.f('ix_proposals_submitted_by'), table_name='proposals')
    op.drop_index(op.f('ix_proposals_rule_type'), table_name='proposals')
    op.drop_index(op.f('ix_proposals_project'), table_name='proposals')
    op.drop_index(op.f('ix_proposals_id'), table_name='proposals')
    op.drop_table('proposals')
    op.drop_index(op.f('ix_feedback_submitted_by'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_rule_id'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_project'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_id'), table_name='feedback')
    op.drop_table('feedback')
    # Explicit enum drop removed; let table definitions handle it
    # ### end Alembic commands ###

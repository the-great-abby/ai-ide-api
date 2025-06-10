"""
Consolidated schema migration: creates all main tables with all columns and indexes in one step.

Revision ID: 20240614_consolidated_schema
Revises: 98d34407c6f1
Create Date: 2024-06-14

# ARR! All UUIDs in this migration are stored as sa.String() for maximum compatibility with SQLAlchemy and Postgres.
# If ye be querying by UUID, always cast to str(uuid_obj) before passing to the DB!
# (Native UUID columns caused many a shipwreck in the past.)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

revision = '20240614_consolidated_schema'
down_revision = '98d34407c6f1'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    # feedback
    if 'feedback' not in inspector.get_table_names():
        op.create_table(
            "feedback",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("rule_id", sa.String(), nullable=True),
            sa.Column("project", sa.String(), nullable=True),
            sa.Column("feedback_type", sa.String(), nullable=True),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column("submitted_by", sa.String(), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_feedback_id", "feedback", ["id"], unique=False)
        op.create_index("ix_feedback_project", "feedback", ["project"], unique=False)
        op.create_index("ix_feedback_rule_id", "feedback", ["rule_id"], unique=False)
        op.create_index("ix_feedback_submitted_by", "feedback", ["submitted_by"], unique=False)

    # proposals
    if 'proposals' not in inspector.get_table_names():
        op.create_table(
            "proposals",
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
            sa.Column("rule_type", sa.String(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("diff", sa.Text(), nullable=True),
            sa.Column("status", sa.String(), nullable=True),
            sa.Column("submitted_by", sa.String(), nullable=True),
            sa.Column("project", sa.UUID(), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=True),
            sa.Column("categories", sa.JSON(), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("examples", sa.JSON(), nullable=True),
            sa.Column("applies_to", sa.JSON(), nullable=True),
            sa.Column("applies_to_rationale", sa.String(), nullable=True),
            sa.Column("reason_for_change", sa.Text(), nullable=True),
            sa.Column("references", sa.Text(), nullable=True),
            sa.Column("current_rule", sa.Text(), nullable=True),
            sa.Column("user_story", sa.Text(), nullable=True),
            sa.Column("scope_level", sa.String(), nullable=False, server_default='global'),
            sa.Column("scope_id", sa.String(), nullable=True),
            sa.Column("parent_rule_id", sa.String(), nullable=True),
            sa.Column("rule_id", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_proposals_id", "proposals", ["id"], unique=False)
        op.create_index("ix_proposals_project", "proposals", ["project"], unique=False)
        op.create_index("ix_proposals_rule_type", "proposals", ["rule_type"], unique=False)
        op.create_index("ix_proposals_submitted_by", "proposals", ["submitted_by"], unique=False)
        op.create_index("ix_proposals_scope_id", "proposals", ["scope_id"], unique=False)
        op.create_index("ix_proposals_scope_level", "proposals", ["scope_level"], unique=False)

    # rules
    if 'rules' not in inspector.get_table_names():
        op.create_table(
            "rules",
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
            sa.Column("rule_type", sa.String(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("diff", sa.Text(), nullable=True),
            sa.Column("status", sa.String(), nullable=True),
            sa.Column("submitted_by", sa.String(), nullable=True),
            sa.Column("added_by", sa.String(), nullable=True),
            sa.Column("project", sa.String(), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=True),
            sa.Column("categories", sa.JSON(), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("examples", sa.JSON(), nullable=True),
            sa.Column("applies_to", sa.JSON(), nullable=True),
            sa.Column("applies_to_rationale", sa.String(), nullable=True),
            sa.Column("user_story", sa.String(), nullable=True),
            sa.Column("scope_level", sa.String(), nullable=True),
            sa.Column("scope_id", sa.String(), nullable=True),
            sa.Column("parent_rule_id", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_rules_added_by", "rules", ["added_by"], unique=False)
        op.create_index("ix_rules_id", "rules", ["id"], unique=False)
        op.create_index("ix_rules_project", "rules", ["project"], unique=False)
        op.create_index("ix_rules_rule_type", "rules", ["rule_type"], unique=False)
        op.create_index("ix_rules_submitted_by", "rules", ["submitted_by"], unique=False)
    else:
        # Patch: If 'examples' column exists and is Text, alter to JSON
        columns = inspector.get_columns('rules')
        for col in columns:
            if col['name'] == 'examples' and str(col['type']).lower().startswith('text'):
                op.alter_column('rules', 'examples', type_=sa.JSON(), postgresql_using='examples::jsonb')

    # rule_versions
    if 'rule_versions' not in inspector.get_table_names():
        op.create_table(
            "rule_versions",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("rule_id", sa.String(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=True),
            sa.Column("rule_type", sa.String(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("diff", sa.Text(), nullable=True),
            sa.Column("status", sa.String(), nullable=True),
            sa.Column("submitted_by", sa.String(), nullable=True),
            sa.Column("added_by", sa.String(), nullable=True),
            sa.Column("project", sa.String(length=255), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.Column("categories", sa.JSON(), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("examples", sa.JSON(), nullable=True),
            sa.Column("applies_to", sa.JSON(), nullable=True),
            sa.Column("applies_to_rationale", sa.String(), nullable=True),
            sa.Column("user_story", sa.Text(), nullable=True),
            sa.Column("scope_level", sa.String(), nullable=True),
            sa.Column("scope_id", sa.String(), nullable=True),
            sa.Column("parent_rule_id", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_rule_versions_id", "rule_versions", ["id"], unique=False)
        op.create_index("ix_rule_versions_rule_id", "rule_versions", ["rule_id"], unique=False)

    # projects
    if 'projects' not in inspector.get_table_names():
        op.create_table(
            "projects",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("default_namespace", sa.String(), nullable=False),
            sa.Column("default_namespace_description", sa.Text(), nullable=True),
            sa.Column("default_namespace_created_at", sa.DateTime(), nullable=True),
            sa.Column("default_namespace_updated_at", sa.DateTime(), nullable=True),
            sa.Column("default_namespace_deleted_at", sa.DateTime(), nullable=True),
            sa.Column("namespace_prefix", sa.String(), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=True, server_default=sa.text('true')),
            sa.Column("has_llm_access", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("created_by", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    # api_access_tokens
    if 'api_access_tokens' not in inspector.get_table_names():
        op.create_table(
            "api_access_tokens",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("token", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("created_by", sa.String(), nullable=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=True),
            sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("allowed_namespaces", postgresql.JSONB, nullable=True),
            sa.Column("namespace_permissions", sa.String(), nullable=True),
            sa.Column("has_llm_access", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("role", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_api_access_tokens_token", "api_access_tokens", ["token"], unique=True)
        op.create_index("ix_api_access_tokens_project_id", "api_access_tokens", ["project_id"], unique=False)

    # bug_reports
    if 'bug_reports' not in inspector.get_table_names():
        op.create_table(
            "bug_reports",
            sa.Column("id", sa.String(), primary_key=True, nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("reporter", sa.String(), nullable=True),
            sa.Column("page", sa.String(), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.Column("user_story", sa.Text(), nullable=True),
        )
    else:
        columns = [col["name"] for col in inspector.get_columns("bug_reports")]
        if "user_story" not in columns:
            op.add_column("bug_reports", sa.Column("user_story", sa.Text(), nullable=True))

    # teams table
    if 'teams' not in inspector.get_table_names():
        op.create_table(
            "teams",
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), unique=True, nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("created_by", sa.String(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=True),
        )

    # enhancements
    if 'enhancements' not in inspector.get_table_names():
        op.create_table(
            "enhancements",
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("suggested_by", sa.String()),
            sa.Column("page", sa.String()),
            sa.Column("tags", sa.String()),
            sa.Column("categories", sa.String()),
            sa.Column("timestamp", sa.DateTime()),
            sa.Column("proposal_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("project", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("status", sa.String(), nullable=True),
            sa.Column("examples", sa.Text(), nullable=True),
            sa.Column("applies_to", sa.String(), nullable=True),
            sa.Column("applies_to_rationale", sa.String(), nullable=True),
            sa.Column("user_story", sa.Text(), nullable=True),
            sa.Column("diff", sa.Text(), nullable=True),
            sa.Column("scope_level", sa.String(), nullable=False, server_default=""),
            sa.Column("scope_id", sa.String(), nullable=True),
            sa.Column("parent_rule_id", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_enhancements_project", "enhancements", ["project"], unique=False)
        op.create_index("ix_enhancements_scope_id", "enhancements", ["scope_id"], unique=False)
        op.create_index("ix_enhancements_scope_level", "enhancements", ["scope_level"], unique=False)

# No downgrade for consolidated migration (irreversible)
def downgrade():
    raise NotImplementedError("This migration cannot be reversed automatically.") 
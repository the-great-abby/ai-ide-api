"""
Convert rules, proposals, and rule_versions JSON columns to JSONB

Revision ID: 8257e00862b4
Revises: 20240614_consolidated_schema
Create Date: 2025-06-09 20:31:29.163841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8257e00862b4'
down_revision: Union[str, None] = '20240614_consolidated_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # rules table
    op.execute("ALTER TABLE rules ALTER COLUMN categories TYPE JSONB USING categories::jsonb;")
    op.execute("ALTER TABLE rules ALTER COLUMN tags TYPE JSONB USING tags::jsonb;")
    op.execute("ALTER TABLE rules ALTER COLUMN examples TYPE JSONB USING examples::jsonb;")
    op.execute("ALTER TABLE rules ALTER COLUMN applies_to TYPE JSONB USING applies_to::jsonb;")
    # proposals table
    op.execute("ALTER TABLE proposals ALTER COLUMN categories TYPE JSONB USING categories::jsonb;")
    op.execute("ALTER TABLE proposals ALTER COLUMN tags TYPE JSONB USING tags::jsonb;")
    op.execute("ALTER TABLE proposals ALTER COLUMN examples TYPE JSONB USING examples::jsonb;")
    op.execute("ALTER TABLE proposals ALTER COLUMN applies_to TYPE JSONB USING applies_to::jsonb;")
    # rule_versions table
    op.execute("ALTER TABLE rule_versions ALTER COLUMN categories TYPE JSONB USING categories::jsonb;")
    op.execute("ALTER TABLE rule_versions ALTER COLUMN tags TYPE JSONB USING tags::jsonb;")
    op.execute("ALTER TABLE rule_versions ALTER COLUMN examples TYPE JSONB USING examples::jsonb;")
    op.execute("ALTER TABLE rule_versions ALTER COLUMN applies_to TYPE JSONB USING applies_to::jsonb;")


def downgrade() -> None:
    """Downgrade schema."""
    # rules table
    op.execute("ALTER TABLE rules ALTER COLUMN categories TYPE JSON USING categories::json;")
    op.execute("ALTER TABLE rules ALTER COLUMN tags TYPE JSON USING tags::json;")
    op.execute("ALTER TABLE rules ALTER COLUMN examples TYPE JSON USING examples::json;")
    op.execute("ALTER TABLE rules ALTER COLUMN applies_to TYPE JSON USING applies_to::json;")
    # proposals table
    op.execute("ALTER TABLE proposals ALTER COLUMN categories TYPE JSON USING categories::json;")
    op.execute("ALTER TABLE proposals ALTER COLUMN tags TYPE JSON USING tags::json;")
    op.execute("ALTER TABLE proposals ALTER COLUMN examples TYPE JSON USING examples::json;")
    op.execute("ALTER TABLE proposals ALTER COLUMN applies_to TYPE JSON USING applies_to::json;")
    # rule_versions table
    op.execute("ALTER TABLE rule_versions ALTER COLUMN categories TYPE JSON USING categories::json;")
    op.execute("ALTER TABLE rule_versions ALTER COLUMN tags TYPE JSON USING tags::json;")
    op.execute("ALTER TABLE rule_versions ALTER COLUMN examples TYPE JSON USING examples::json;")
    op.execute("ALTER TABLE rule_versions ALTER COLUMN applies_to TYPE JSON USING applies_to::json;")

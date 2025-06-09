"""add bug_reports table for in-app bug reporting

Revision ID: d4034974e03f
Revises: 0004_create_rules
Create Date: 2025-05-17 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "d4034974e03f"
down_revision: Union[str, None] = "20240603_alter_alembic_version_num_length"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    print("DEBUG: Inspector tables at start of migration:", inspector.get_table_names())
    print("DEBUG: Inspector default schema:", inspector.default_schema_name)
    try:
        # Only create the table if it doesn't exist
        if "bug_reports" not in inspector.get_table_names():
            op.create_table(
                "bug_reports",
                sa.Column("id", sa.String(), primary_key=True),
                sa.Column("description", sa.Text()),
                sa.Column("reporter", sa.String()),
                sa.Column("page", sa.String()),
                sa.Column("timestamp", sa.DateTime()),
            )
            print("DEBUG: bug_reports table creation code executed!")
        # Always create a test table for debugging
        op.create_table(
            "always_create_test",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("note", sa.Text()),
        )
        print("DEBUG: always_create_test table creation code executed!")
        # Try raw SQL table creation
        op.execute("CREATE TABLE IF NOT EXISTS raw_sql_test (id serial PRIMARY KEY, note text);")
        print("DEBUG: raw_sql_test table creation via raw SQL executed!")
    except Exception as e:
        print(f"DEBUG: Exception during table creation: {e}")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("bug_reports")

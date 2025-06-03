"""Convert allowed_namespaces to JSONB in api_access_tokens

Revision ID: 20240603_convert_allowed_namespaces_to_jsonb
Revises: add_namespace_permissions
Create Date: 2024-06-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = "20240603_convert_allowed_namespaces_to_jsonb"
down_revision: Union[str, None] = "add_namespace_permissions"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "api_access_tokens" in inspector.get_table_names():
        columns = inspector.get_columns("api_access_tokens")
        for col in columns:
            if col["name"] == "allowed_namespaces":
                # Only convert if type is ARRAY
                if str(col["type"]).startswith("ARRAY"):
                    op.execute(
                        text(
                            "ALTER TABLE api_access_tokens ALTER COLUMN allowed_namespaces TYPE JSONB USING to_jsonb(allowed_namespaces);"
                        )
                    )
                break

def downgrade() -> None:
    # Downgrade not implemented (would require converting JSONB back to ARRAY)
    pass 
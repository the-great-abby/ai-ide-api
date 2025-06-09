"""Fix project_id type to UUID in api_access_tokens and namespace_permissions

Revision ID: 656e27e6240a
Revises: c8846f51d98d
Create Date: 2025-06-05 07:59:46.346519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '656e27e6240a'
down_revision: Union[str, None] = 'c8846f51d98d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Arrr matey! All api_access_tokens- and namespace_permissions-related schema changes be handled in the consolidated migration. This migration be a no-op. Hoist the Jolly Roger!
    # Convert namespace_permissions.project_id from VARCHAR to UUID if needed


def downgrade() -> None:
    """Downgrade schema."""
    # Arrr matey! All api_access_tokens- and namespace_permissions-related schema changes be handled in the consolidated migration. This migration be a no-op. Hoist the Jolly Roger!
    # Revert namespace_permissions.project_id from UUID to VARCHAR if needed

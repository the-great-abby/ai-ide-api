"""merge uuid and other heads

Revision ID: d82e291c4873
Revises: 20240526_update_proposal_uuids, c8b957ff43ca
Create Date: 2025-05-26 15:56:05.791036

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d82e291c4873"
down_revision: Union[str, None] = ("20240526_update_proposal_uuids", "c8b957ff43ca")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""
Merge heads f281313beb28 and fd273470995c

Revision ID: merge_f281313beb28_and_fd273470995c
Revises: f281313beb28, fd273470995c
Create Date: 2024-06-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'merge_f281313beb28_and_fd273470995c'
down_revision: Union[str, None] = 'f281313beb28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass 
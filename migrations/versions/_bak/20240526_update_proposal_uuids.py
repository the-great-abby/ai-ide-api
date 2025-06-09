"""
ARR! This migration be obsolete! All UUIDs are now stored as sa.String() for maximum compatibility. See ONBOARDING_INTERNAL.md and rules/db_types.mdc for the tale.

Update UUID fields in proposals table

Revision ID: 20240526_update_proposal_uuids
Revises: d912b78b75b4
Create Date: 2025-05-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "20240526_update_proposal_uuids"
down_revision: Union[str, None] = "d912b78b75b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    # Ensure rules.id is UUID before creating the foreign key
    if "rules" in inspector.get_table_names():
        op.alter_column(
            "rules",
            "id",
            type_=sa.UUID(as_uuid=True),
            postgresql_using="id::uuid",
            existing_type=sa.String(),
            nullable=False,
        )

    # Update proposals table
    if "proposals" in inspector.get_table_names():
        # Drop foreign key constraints first
        for fk in inspector.get_foreign_keys("proposals"):
            op.drop_constraint(fk["name"], "proposals")

        # Drop indexes that will be recreated
        for idx in inspector.get_indexes("proposals"):
            if idx["name"] in [
                "ix_proposals_id",
                "ix_proposals_rule_id",
                "ix_proposals_parent_rule_id",
            ]:
                op.drop_index(idx["name"], "proposals")

        # Alter columns to UUID type
        op.alter_column(
            "proposals",
            "id",
            type_=sa.UUID(as_uuid=True),
            postgresql_using="id::uuid",
            existing_type=sa.String(),
            nullable=False,
        )

        op.alter_column(
            "proposals",
            "rule_id",
            type_=sa.UUID(as_uuid=True),
            postgresql_using="rule_id::uuid",
            existing_type=sa.String(),
            nullable=True,
        )

        op.alter_column(
            "proposals",
            "parent_rule_id",
            type_=sa.UUID(as_uuid=True),
            postgresql_using="parent_rule_id::uuid",
            existing_type=sa.String(),
            nullable=True,
        )

        # Recreate indexes
        op.create_index("ix_proposals_id", "proposals", ["id"], unique=False)
        op.create_index("ix_proposals_rule_id", "proposals", ["rule_id"], unique=False)
        op.create_index(
            "ix_proposals_parent_rule_id", "proposals", ["parent_rule_id"], unique=False
        )

        # Recreate foreign key constraints
        op.create_foreign_key(
            "fk_proposals_rule_id", "proposals", "rules", ["rule_id"], ["id"]
        )
        op.create_foreign_key(
            "fk_proposals_parent_rule_id",
            "proposals",
            "rules",
            ["parent_rule_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    # Update proposals table
    if "proposals" in inspector.get_table_names():
        # Drop foreign key constraints first
        for fk in inspector.get_foreign_keys("proposals"):
            op.drop_constraint(fk["name"], "proposals")

        # Drop indexes that will be recreated
        for idx in inspector.get_indexes("proposals"):
            if idx["name"] in [
                "ix_proposals_id",
                "ix_proposals_rule_id",
                "ix_proposals_parent_rule_id",
            ]:
                op.drop_index(idx["name"], "proposals")

        # Alter columns back to String type
        op.alter_column(
            "proposals",
            "id",
            type_=sa.String(),
            postgresql_using="id::text",
            existing_type=sa.UUID(as_uuid=True),
            nullable=False,
        )

        op.alter_column(
            "proposals",
            "rule_id",
            type_=sa.String(),
            postgresql_using="rule_id::text",
            existing_type=sa.UUID(as_uuid=True),
            nullable=True,
        )

        op.alter_column(
            "proposals",
            "parent_rule_id",
            type_=sa.String(),
            postgresql_using="parent_rule_id::text",
            existing_type=sa.UUID(as_uuid=True),
            nullable=True,
        )

        # Recreate indexes
        op.create_index("ix_proposals_id", "proposals", ["id"], unique=False)
        op.create_index("ix_proposals_rule_id", "proposals", ["rule_id"], unique=False)
        op.create_index(
            "ix_proposals_parent_rule_id", "proposals", ["parent_rule_id"], unique=False
        )

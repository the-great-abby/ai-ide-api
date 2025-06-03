"""create memory_edges and memory_vectors with vector(768)

Revision ID: 20250518_create_memorydb_schema
Revises: 
Create Date: 2025-05-18

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250518_create_memorydb_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Ensure pgvector extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Create memory_edges table
    op.execute(
        """
        CREATE TABLE memory_edges (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            from_id UUID,
            to_id UUID,
            relation_type VARCHAR,
            meta TEXT,
            created_at TIMESTAMP
        );
    """
    )

    # Create memory_vectors table with 768-dim vector
    op.execute(
        """
        CREATE TABLE memory_vectors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            namespace VARCHAR,
            reference_id VARCHAR,
            content TEXT NOT NULL,
            embedding vector(768),
            meta TEXT,
            created_at TIMESTAMP,
            project_id UUID
        );
    """
    )

    # Add indexes
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_edges_from_id ON memory_edges (from_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_edges_to_id ON memory_edges (to_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_edges_relation_type ON memory_edges (relation_type);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_vectors_namespace ON memory_vectors (namespace);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_vectors_reference_id ON memory_vectors (reference_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_vectors_project_id ON memory_vectors (project_id);"
    )

    # Patch: Ensure alembic_version.version_num is VARCHAR(255) for long revision IDs
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);")


def downgrade():
    op.execute("DROP TABLE IF EXISTS memory_edges;")
    op.execute("DROP TABLE IF EXISTS memory_vectors;")
    # Optionally, drop the extension if you want a clean slate:
    # op.execute("DROP EXTENSION IF EXISTS vector CASCADE;")

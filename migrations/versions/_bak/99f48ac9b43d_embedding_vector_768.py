"""embedding_vector_768

Revision ID: 99f48ac9b43d
Revises: b3c4d5e6f7a8_project_indexes
Create Date: 2025-05-18 20:21:38.774107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99f48ac9b43d'
down_revision: Union[str, None] = 'b3c4d5e6f7a8_project_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # WARNING: This will drop the entire memory_vectors table and the vector extension! All data will be lost.
    op.execute("DROP TABLE IF EXISTS memory_vectors;")
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE;")
    op.execute("CREATE EXTENSION vector;")
    op.execute("""
        CREATE TABLE memory_vectors (
            id VARCHAR PRIMARY KEY,
            namespace VARCHAR,
            reference_id VARCHAR,
            content TEXT NOT NULL,
            embedding vector(768),
            meta TEXT,
            created_at TIMESTAMP
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_memory_vectors_namespace ON memory_vectors (namespace);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_memory_vectors_reference_id ON memory_vectors (reference_id);")


def downgrade() -> None:
    """Downgrade schema."""
    # WARNING: This will drop the entire memory_vectors table and the vector extension! All data will be lost.
    op.execute("DROP TABLE IF EXISTS memory_vectors;")
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE;")
    op.execute("CREATE EXTENSION vector;")
    op.execute("""
        CREATE TABLE memory_vectors (
            id VARCHAR PRIMARY KEY,
            namespace VARCHAR,
            reference_id VARCHAR,
            content TEXT NOT NULL,
            embedding vector(1536),
            meta TEXT,
            created_at TIMESTAMP
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_memory_vectors_namespace ON memory_vectors (namespace);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_memory_vectors_reference_id ON memory_vectors (reference_id);")

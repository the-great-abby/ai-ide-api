-- 01_create_memorydb.sql
-- Create the databases if they don't exist
CREATE DATABASE rulesdb;
CREATE DATABASE memorydb;

-- Connect to rulesdb to install pgvector
\connect rulesdb;
CREATE EXTENSION IF NOT EXISTS vector;

-- Pre-create alembic_version table with VARCHAR(255) for long revision IDs
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(255) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Connect to memorydb to install pgvector
\connect memorydb;
CREATE EXTENSION IF NOT EXISTS vector; 
-- 01_create_memorydb.sql
-- Create the databases if they don't exist
CREATE DATABASE rulesdb;
CREATE DATABASE memorydb;

-- Connect to rulesdb to install pgvector and pg_trgm
\connect rulesdb;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Pre-create alembic_version table with VARCHAR(255) for long revision IDs
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(255) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Connect to memorydb to install pgvector and pg_trgm
\connect memorydb;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Pre-create alembic_version table with VARCHAR(255) for long revision IDs in memorydb
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(255) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
); 
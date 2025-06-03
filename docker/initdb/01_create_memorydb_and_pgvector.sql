-- 01_create_memorydb.sql
-- Create the databases if they don't exist
CREATE DATABASE rulesdb;
CREATE DATABASE memorydb;

-- Connect to rulesdb to install pgvector
\connect rulesdb;
CREATE EXTENSION IF NOT EXISTS vector;

-- Connect to memorydb to install pgvector
\connect memorydb;
CREATE EXTENSION IF NOT EXISTS vector; 
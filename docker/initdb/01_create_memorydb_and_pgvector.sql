-- 01_create_memorydb.sql
CREATE DATABASE memorydb;

-- Install pgvector in rulesdb (if not already present)
\connect rulesdb
CREATE EXTENSION IF NOT EXISTS vector;

-- Install pgvector in memorydb
\connect memorydb
CREATE EXTENSION IF NOT EXISTS vector; 
# Troubleshooting: memory_vectors embedding column and pgvector type

## Problem

When running migrations or recreating models, you may encounter errors like:

- `psycopg2.errors.UndefinedFunction: operator does not exist: double precision[] <=> double precision[]`
- Vector search queries fail with errors about the `<=>` operator or missing `vector` type.

## Causes

1. **embedding column is an array, not a pgvector type**
   - The migration creates `embedding` as `ARRAY(Float)` instead of `VECTOR` (pgvector extension).
   - The model uses a custom `Vector` type, but Alembic or manual migrations may default to arrays.

2. **memory_vectors table created in the wrong database**
   - The table is created in `rulesdb` instead of `memorydb`.
   - Vector search and memory endpoints expect the table in `memorydb`.

## How to Fix

### 1. Ensure the embedding column uses pgvector
- In your migration, use:
  ```python
  sa.Column("embedding", sa.dialects.postgresql.VECTOR(768), nullable=True)
  ```
- Do **not** use `ARRAY(Float)` for embeddings if you want pgvector support.
- If the table already exists as an array, you must drop and recreate it with the correct type.

### 2. Ensure the table is created in memorydb
- Check your migration and DB engine bindings.
- Run migrations for `memorydb` using the correct Alembic config (e.g., `alembic_memorydb.ini`).
- Do **not** create memory tables in `rulesdb`.

## Best Practices
- Always check the schema after running migrations:
  ```sh
  psql -U postgres -d memorydb -c '\d+ memory_vectors'
  ```
- Confirm `embedding` is of type `vector`.
- Confirm the table exists in `memorydb`, not `rulesdb`.

## References
- [pgvector documentation](https://github.com/pgvector/pgvector)
- See also: ONBOARDING_INTERNAL.md, rules/db_types.mdc 
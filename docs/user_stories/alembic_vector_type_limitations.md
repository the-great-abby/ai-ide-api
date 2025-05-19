# User Story: Alembic Limitations with Vector and Custom Postgres Types

## Motivation
As a developer or maintainer, I want to understand the limitations of Alembic (and SQLAlchemy migrations in general) when working with custom Postgres types like `pgvector`, so I can avoid migration errors and ensure reliable schema evolution.

## Actors
- Developers
- DevOps engineers
- AI system maintainers

## Problem / Symptoms
- Alembic autogeneration does not natively recognize custom types (e.g., `db.Vector()`, `pgvector`), leading to broken or incomplete migration scripts.
- Migration scripts may reference undefined symbols (e.g., `db.Vector()`), causing `NameError` or similar errors during migration.
- Downgrade/upgrade steps for custom types may be missing or incorrect.
- Raw SQL may be required for certain operations (e.g., creating or altering vector columns).

## Step-by-Step Actions
1. Developer updates a model to add or modify a vector/custom type column (e.g., `embedding = Column(Vector(1536))`).
2. Developer runs Alembic autogenerate to create a migration revision.
3. Alembic generates a migration script that may include references to `db.Vector()` or other custom types.
4. **Manual intervention is required:**
    - Edit the migration script to use the correct SQLAlchemy type (e.g., `sa.String`, `sa.Text`) or raw SQL for the custom type.
    - For `pgvector`, use `sa.types.UserDefinedType` or `op.execute()` with raw SQL (e.g., `ALTER TABLE ... ADD COLUMN embedding vector(1536);`).
5. Test the migration in a dev environment before applying to production.

## Best Practices
- **Always review and manually edit Alembic migration scripts** when custom types are involved.
- **For migrations:** Prefer raw SQL (e.g., `op.execute(...)`) for custom types like `pgvector` to ensure correct DDL is applied.
- **For models:** Use `UserDefinedType` in your SQLAlchemy models for clarity and type safety.
- Use raw SQL in migrations for operations Alembic/SQLAlchemy cannot express (e.g., `op.execute("ALTER TABLE ...")`).
- Document manual steps and rationale in the migration script comments.
- Add tests to verify that migrations succeed and the schema is correct.
- Keep a reference of working migration patterns for custom types.

## Summary & Guidance
- **Migrations:** Use raw SQL for schema changes involving custom types (e.g., `pgvector`). This avoids Alembic/SQLAlchemy confusion and ensures the correct SQL is run.
- **Models:** Use a custom `UserDefinedType` for your SQLAlchemy models to keep your code clean and type-safe.
- **Why:** Alembic's autogeneration and SQLAlchemy's type system do not natively handle all custom types, so explicit handling is required for reliability.

## Example: Fixing a Migration Script
**Problematic autogen output:**
```python
sa.Column('embedding', db.Vector(), nullable=True),  # This will fail: db is not defined
```

**Manual fix:**
```python
op.execute('ALTER TABLE memory_vectors ADD COLUMN embedding vector(1536);')
# Or, if using SQLAlchemy's UserDefinedType:
# sa.Column('embedding', sa.types.UserDefinedType(), nullable=True)
```

## References
- [pgvector docs](https://github.com/pgvector/pgvector)
- [SQLAlchemy custom types](https://docs.sqlalchemy.org/en/20/core/custom_types.html)
- [Alembic operations](https://alembic.sqlalchemy.org/en/latest/ops.html)
- [ai_memory_vector_sqlalchemy_limitations.md](ai_memory_vector_sqlalchemy_limitations.md)

## See Also
- [ai_memory_vector_sqlalchemy_limitations.md](ai_memory_vector_sqlalchemy_limitations.md)
- [bug_report_with_user_story.md](bug_report_with_user_story.md) 
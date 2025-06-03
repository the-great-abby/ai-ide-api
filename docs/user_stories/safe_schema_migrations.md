# User Story: Safe Schema Migrations with Existence Checks

## Motivation
Schema migrations can fail or cause downtime if they attempt to create tables or columns that already exist, or alter structures that are missing. To ensure robust, repeatable, and collaborative migrations, all migration scripts should check for the existence of tables and columns before creating or altering them.

## Actors
- Developers
- DevOps engineers
- Database administrators
- CI/CD systems

## Preconditions
- A project uses Alembic (or similar) for database migrations.
- The codebase may have multiple contributors and/or long-lived branches.

## Steps
1. When writing a migration, use SQLAlchemy's inspector to check if a table or column exists before creating or altering it.
2. If the table/column does not exist, proceed with the creation or alteration.
3. If it already exists, skip the operation to avoid errors.
4. Apply this pattern to all new migrations and, when possible, refactor older migrations for consistency.
5. Run migrations in CI/CD and local environments to verify idempotency and safety.

## Example (Alembic/SQLAlchemy)
```python
bind = op.get_bind()
inspector = inspect(bind)
if 'my_table' in inspector.get_table_names():
    columns = [c['name'] for c in inspector.get_columns('my_table')]
    if 'my_column' not in columns:
        op.add_column('my_table', sa.Column('my_column', sa.String()))
```

## Expected Outcomes
- Migrations are idempotent and safe to run multiple times.
- Developers avoid common migration errors (DuplicateTable, DuplicateColumn, etc).
- CI/CD pipelines are more reliable.
- Production deployments are less risky.

## Best Practices
- Always check for existence before creating or altering tables/columns.
- Use SQLAlchemy's inspector for checks in Alembic migrations.
- Document this pattern in onboarding and code review guidelines.
- Refactor legacy migrations as time allows.

## References
- [Alembic Operations](https://alembic.sqlalchemy.org/en/latest/ops.html)
- [SQLAlchemy Inspector](https://docs.sqlalchemy.org/en/20/core/inspection.html) 
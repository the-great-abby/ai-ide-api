# Alembic Version Table Customization for Long Revision IDs

## Rationale
By default, Alembic creates the `alembic_version` table with `version_num VARCHAR(32)`. This limits revision IDs to 32 characters. To support longer revision IDs (e.g., for descriptive merge migrations), we pre-create the table with `VARCHAR(255)` during the database initialization (initdb) step.

## Implementation
- The following SQL is included in the Docker/Postgres `initdb` scripts:
  ```sql
  CREATE TABLE IF NOT EXISTS alembic_version (
      version_num VARCHAR(255) NOT NULL,
      CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
  );
  ```
- This ensures that when Alembic runs, it will use the existing table with the larger column size, allowing long revision IDs from the very first migration.
- The Alembic migration that alters the column type is not needed and can be removed or made a no-op.

## Maintenance Notes
- If the `alembic_version` table is ever dropped, it must be recreated with `VARCHAR(255)` before running Alembic again.
- This requirement applies to all environments: dev, test, prod, and CI/CD.
- Document this in onboarding and ops docs, and ensure all team members are aware.

## References
- [Alembic documentation: The alembic_version table](https://alembic.sqlalchemy.org/en/latest/tutorial.html#the-alembic-version-table) 
# User Story: Checking and Applying Database Migrations

## Motivation
As a developer or system administrator, I want to ensure that the database schema is always in sync with the latest codebase, so that new features, bug fixes, and data models work as intended and no migrations are missed.

## Actors
- Developer
- System Administrator

## Preconditions
- The project uses Alembic for database migrations.
- The database and API services are running via Docker Compose.
- You have access to the project codebase and Makefile.ai.

## Step-by-Step Actions

### 1. **Check for Recent Migration Changes**
- Run:
  ```bash
  git log --since='24 hours ago' --name-only | grep migrations/versions/
  ```
- Or review PRs/commits for migration files.

### 2. **Check Migration History**
- With Makefile.ai (if available):
  ```bash
  make -f Makefile.ai ai-db-history
  ```
- Or manually:
  ```bash
  docker compose exec api alembic history --verbose
  ```

### 3. **Apply Unapplied Migrations**
- With Makefile.ai (if available):
  ```bash
  make -f Makefile.ai ai-db-upgrade
  ```
- Or manually:
  ```bash
  docker compose exec api alembic upgrade head
  ```

### 4. **Verify Migration Status**
- Check for errors in the output.
- Optionally, inspect the database schema or use:
  ```bash
  docker compose exec api alembic current
  ```

## Expected Outcomes
- The database schema matches the latest codebase.
- All migrations are applied in order.
- No errors or missing tables/columns.

## Troubleshooting
- **Migration fails:**
  - Check for merge conflicts in migration files.
  - Ensure the database service is running.
  - Review Alembic error messages for missing dependencies or syntax errors.
- **Makefile target missing:**
  - Use the manual Docker Compose/Alembic commands above.

## Best Practices
- Always check for unapplied migrations after pulling new code or switching branches.
- Run migrations before starting the API or backend services if possible.
- Keep migration files small and focused.
- Resolve merge conflicts in migration files promptly.
- Document new migrations in PRs and changelogs.

## References
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Makefile.ai targets](../Makefile.ai) 
# User Story: Update Models, Generate Migrations, Apply, and Reset DB

## Motivation
As a developer, I want a clear, repeatable workflow for updating database models, generating and applying Alembic migrations, and resetting the test database, so that schema changes are robust, testable, and easy to recover from.

## Actors
- Developer
- System Administrator
- CI/CD pipeline

## Preconditions
- The project uses SQLAlchemy models and Alembic for migrations.
- The database runs in Docker Compose (e.g., `rulesdb`, `memorydb`).
- Makefile targets are available for migration and DB management.

## Step-by-Step Actions

### 1. **Update Models**
- Edit SQLAlchemy models (e.g., change column types, add/remove fields).
- Example: Migrate all `id` and `project_id` columns to `UUID` type for consistency and future-proofing.

### 2. **Generate Alembic Migration**
- Ensure the database is up to date:
  ```bash
  make -f Makefile.ai-db ai-db-migrate
  ```
- Generate a new migration reflecting model changes:
  ```bash
  make -f Makefile.ai-db ai-db-revision MSG="Describe your schema change"
  ```

### 3. **Apply Migrations**
- Apply all migrations to the database:
  ```bash
  make -f Makefile.ai-db ai-db-migrate
  ```
- If you encounter errors (e.g., type mismatches), resolve them in the models and migration scripts, then repeat.

### 4. **Reset and Set Up the Test Database**
- Use the `ai-test-clean` target to drop, recreate, and migrate both `rulesdb` and `memorydb`:
  ```bash
  make -f Makefile.ai ai-test-clean
  ```
- This ensures a clean slate for tests and development.

### 5. **Set Up Database, Onboard Admin, and Run Tests (Preferred)**
- Use the `ai-test-with-setup` target to:
  - Start required services (db-test, api)
  - Wait for the database to be ready
  - Create the `rulesdb` database if missing
  - Run all migrations (main and memorydb)
  - **Run onboarding to create the admin token (via `ai-onboard-admin`)**
  - Run the full test suite
  
  ```bash
  make -f Makefile.ai ai-test-with-setup
  ```
- This is now the **preferred workflow** for running tests after a reset or migration change, as it ensures the database is freshly set up, all migrations are applied, and onboarding is performed before testing.
- For verbose output, use:
  ```bash
  make -f Makefile.ai ai-test-with-setup-verbose
  ```
- For coverage:
  ```bash
  make -f Makefile.ai ai-test-with-setup-coverage
  ```

## Expected Outcomes
- Database schema matches the latest models.
- All migrations are applied in order, with no errors.
- Test database is clean and ready for use.
- Tests pass, confirming schema and migration correctness.

## Best Practices
- Always apply outstanding migrations before generating new ones.
- Use UUIDs for primary and foreign keys for consistency.
- Use Makefile targets for all migration and DB operations.
- **Use `ai-test-with-setup` for a fresh, reliable test run after DB/model changes.**
- Use `ai-test-clean` for a full DB reset before setup/testing if needed.
- Document new workflows and targets in user stories and onboarding docs.
- Reference this user story in code reviews and onboarding.
- **Note:** Alembic does not handle custom types like `vector(768)` (pgvector) well. For schema changes involving these columns, use raw SQL with `op.execute` and review generated migrations carefully.

## Warnings
- If you need to change a `vector(768)` column (pgvector), do not rely on Alembic's autogenerate. Write manual SQL in your migration, and be aware that autogenerate may not detect or handle these types correctly.

## References
- [Safe Schema Migrations](./safe_schema_migrations.md)
- [Database Migration Recovery & Stamping](./db_migration_recovery_and_stamping.md)
- [Checking and Applying Database Migrations](./database_migrations.md)
- **After nuking or resetting the database, always run onboarding (`make -f Makefile.ai ai-onboard-admin`) before running tests if not using `ai-test-with-setup`.** 
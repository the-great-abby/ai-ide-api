# Troubleshooting: Disappearing `superseded_by` Column in `rules` Table

## Problem
After nuking the test DB and running migrations, the `superseded_by` column exists in the `rules` table. After running the test suite, the column disappears, causing test failures.

---

## 1. Initial Observations
- `superseded_by` is present in the base migration and SQLAlchemy model.
- After migrations: column is present.
- After tests: column is missing, causing errors.

## 2. What Was Checked
- **Migration Files:** No migration drops or removes the column.
- **Test Code:** No test calls `create_all`, `drop_all`, or `init_db`. No raw SQL in Python code drops or recreates the table.
- **Model Definition:** The `Rule` model in `db.py` correctly defines the `superseded_by` column.
- **Subprocesses/Workers:** No subprocesses or test workers are running migrations or schema changes during tests.
- **Test Output:** No log evidence of schema changes, only errors about the missing column.

## 3. Step-by-Step Experiment
- Nuked the DB and confirmed it was empty.
- Ran migrations: `rules.superseded_by` column was present.
- Ran tests: column disappeared, tests failed.
- Re-inspected DB: column was missing.

## 4. Hypotheses and Rulings
- No test or migration is explicitly removing the column.
- No subprocess or parallel test worker is altering the schema.
- The most likely cause is a test, fixture, or app startup code that is recreating the table using an outdated model or metadata, or the test DB is being swapped out for a different one during the test run.

## 5. Next Steps
- Search for any code that might be recreating the schema with outdated metadata.
- Add logging to catch schema changes during test or app startup.
- Consider checking table OIDs or creation times before and after tests to detect recreation.

---

## Root Cause and Solution (2025-06-13)
- **MemoryDB migrations were not running successfully due to alembic_version.version_num being too short (VARCHAR(32)).**
- The init scripts did create alembic_version as VARCHAR(255), but if the table already existed from a previous volume, it was not updated.
- **Solution:**
  - Nuke all Docker volumes and containers related to the test and memory databases.
  - Re-run the init scripts and migrations from a clean slate.
  - Confirm that both rulesdb and memorydb have the correct schema and that alembic_version.version_num is long enough for your migration IDs.
  - After this, all migrations and tests ran as expected, and the schema remained correct throughout the test run.

## Lessons Learned
- Always nuke all relevant Docker volumes and containers when troubleshooting persistent DB schema issues.
- Ensure your alembic_version table supports long migration IDs (VARCHAR(128) or VARCHAR(255)).
- If you use `CREATE TABLE IF NOT EXISTS`, it will not update an existing table—run an explicit `ALTER TABLE` if needed.
- Add granular logging to test fixtures and hooks to pinpoint exactly when schema changes occur.
- If a migration fails, always check the logs for errors about schema or data type mismatches.
- Once the DB infrastructure is correct, remaining test failures are likely real application or validation issues, not migration problems.

## Best Practices
- Always use incremental migrations for schema changes, even if the base migration is updated.
- Add debug logging at test startup to capture the actual schema as seen by the test code.
- Regularly clean up old Docker volumes and containers to avoid stale schema issues. 
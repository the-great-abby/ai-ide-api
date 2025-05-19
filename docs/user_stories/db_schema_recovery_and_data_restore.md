# User Story: Database Schema Recovery and Data-Only Restore

**As a developer or maintainer,**
I want to safely recover from database schema issues (such as missing columns after migrations)
and restore my data without losing records,
so that I can quickly get the system back to a working state after migration or schema drift problems.

---

## Acceptance Criteria
- I can back up my data (data-only) before making destructive changes.
- I can nuke (reset) the database and volumes safely.
- I can re-apply all migrations to get a clean, up-to-date schema.
- I can restore my data into the new schema.
- The process is documented and repeatable using Makefile targets.
- Troubleshooting tips are included for common issues (e.g., Alembic version errors).

---

## Example Workflow

1. **Backup data only (ALWAYS do this before running `docker compose down -v` or any destructive operation):**
   ```bash
   make -f Makefile.ai ai-db-backup-data-only
   # Backup is saved in backups/rulesdb-data-YYYYMMDD-HHMMSS.sql
   ```

2. **Nuke the database and all volumes (e.g., for frontend rebuild troubleshooting):**
   ```bash
   docker compose down -v
   # This will stop all containers and remove all volumes, including the database!
   ```

3. **Start up services and wait for API:**
   ```bash
   make -f Makefile.ai ai-up
   # (ai-up now waits for the API to be ready)
   ```

4. **Run all migrations:**
   ```bash
   make -f Makefile.ai ai-db-migrate
   ```

5. **Verify schema (optional):**
   ```bash
   make -f Makefile.ai schema-table TABLE=rules
   # Check for expected columns (e.g., user_story)
   ```

6. **Restore data:**
   ```bash
   # Use the most recent backup file
   make -f Makefile.ai ai-db-restore-data BACKUP=backups/rulesdb-data-YYYYMMDD-HHMMSS.sql
   ```

---

## Troubleshooting
- **Duplicate alembic_version error:**
  - This is safe to ignore during data-only restore; it does not affect your schema or main data.
- **Schema mismatch after restore:**
  - Ensure you ran all migrations before restoring data.
- **UI/API errors after restore:**
  - Check logs with `make -f Makefile.ai logs-api` and verify schema with `schema-table` target.

---

## References
- [Makefile.ai targets](../Makefile.ai)
- [ONBOARDING.md](../ONBOARDING.md)
- [Database backup and restore rules](../.cursor/rules/db_backup.mdc) 
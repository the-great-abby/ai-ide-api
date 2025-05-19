# Backup and Restore for rulesdb and memorydb

> ## Proven and Recommended Workflow (2025-05-17)
> This user story and the steps below reflect the latest, tested, and recommended method for full backup, migration, and restore of both rulesdb and memorydb. This workflow has been validated end-to-end and should be used for disaster recovery, onboarding, and environment migration.
>
> - Both schema and data can be reliably restored for both databases.
> - Data-only restores are supported and tested for both rulesdb and memorydb.
> - The process is robust against duplicate key errors and schema/index mismatches.
> - This is the standard for all future backup/restore operations.
>
> _Last updated: 2025-05-17_

## Motivation
Ensure all critical data (rules, projects, vectors, etc.) can be reliably backed up and restored, including both the main (rulesdb) and memory (memorydb) databases.

## Actors
- System Admin
- Developer

## Preconditions
- Docker and Makefile.ai are available
- Databases are running in Docker (API does NOT need to be up for migrations)

## Steps
### 1. Backing Up
- To back up both databases (full):
  - `make -f Makefile.ai ai-db-backup-all`
- To back up only rulesdb (full):
  - `make -f Makefile.ai ai-db-backup`
- To back up only memorydb (full):
  - `make -f Makefile.ai ai-memorydb-backup`
- To back up only the schema:
  - `make -f Makefile.ai ai-memorydb-schema-backup`
- To back up only the data:
  - `make -f Makefile.ai ai-db-backup-data-only` (rulesdb)
  - `make -f Makefile.ai ai-memorydb-backup-data-only` (memorydb)

### 2. Restoring
- To restore both databases (full):
  - `make -f Makefile.ai ai-db-restore-all RULESDB_FILE=backups/rulesdb-YYYYMMDD-HHMMSS.sql MEMORYDB_FILE=backups/memorydb-YYYYMMDD-HHMMSS.sql`
- To restore only rulesdb (full):
  - `make -f Makefile.ai ai-db-restore BACKUP=backups/rulesdb-YYYYMMDD-HHMMSS.sql`
- To restore only memorydb (full):
  - `make -f Makefile.ai ai-memorydb-restore BACKUP_FILE=backups/memorydb-latest.sql`
- To restore only the data:
  - `make -f Makefile.ai ai-db-restore-data BACKUP=backups/rulesdb-data-YYYYMMDD-HHMMSS.sql` (rulesdb)
  - `make -f Makefile.ai ai-memorydb-restore-data BACKUP_FILE=backups/memorydb-data-YYYYMMDD-HHMMSS.sql` (memorydb)

### 3. Full Database Reset, Migration, and Restore
- To completely reset, migrate, and restore your databases:
  1. **Nuke the database (removes all data/volumes):**
     - `make -f Makefile.ai ai-db-nuke`
  2. **Bring up the database:**
     - `make -f Makefile.ai ai-db-up`
  3. **Run migrations (only the database needs to be up):**
     - `make -f Makefile.ai ai-db-migrate`
  4. **Restore your data:**
     - `make -f Makefile.ai ai-memorydb-restore-data BACKUP_FILE=backups/memorydb-data-YYYYMMDD-HHMMSS.sql`
     - (Optional) Restore rulesdb data as well
  5. **(Optional) Bring up API and frontend:**
     - `make -f Makefile.ai ai-up`

## Expected Outcomes
- All data and schema can be reliably backed up and restored for both databases.
- Data-only backups allow for fast migration or recovery without affecting schema.
- Migrations can be run as soon as the database is up; the API does not need to be running.

## Best Practices
- Store all backups in the `backups/` directory with timestamps.
- Automate backups (e.g., nightly cron job or CI/CD pipeline).
- Test restores regularly to ensure backup validity.
- Always restore schema before restoring data-only backups.
- Document backup/restore steps in onboarding and admin docs.

## 🛡️ AI-Friendly Backup/Restore Disaster Recovery Test Workflow

This workflow is the recommended, validated method for disaster recovery and automated test verification. It is split into two phases for safety and automation:

### 1. Setup Phase (Data Creation)
- Run the test to create unique test data in the API and databases:
  ```bash
  make -f Makefile.ai ai-test-backup-restore
  ```
- The test will print instructions to run the backup/restore script and then exit.

### 2. Backup/Restore Cycle (Host Script)
- On your host (not in a container), run the provided script to:
  - Backup both databases (data-only)
  - Nuke the databases
  - Bring up API/DB and run migrations
  - Restore both databases (data-only)
  ```bash
  bash scripts/backup_restore_cycle.sh
  ```

### 3. Verification Phase (Data Integrity Check)
- Re-run the test in verification mode to confirm all data was restored correctly:
  ```bash
  BACKUP_RESTORE_PHASE=verify make -f Makefile.ai ai-test-backup-restore
  ```

#### Environment Variable
- `BACKUP_RESTORE_PHASE` controls which phase runs:
  - `setup` (default): Create data and instruct to run the host script.
  - `verify`: Check data integrity after restore.

#### Why this is AI-friendly
- The workflow is modular and safe for automation:
  - Test logic is portable and can be run by AI agents or CI/CD.
  - Destructive operations are isolated in a host script for auditability and safety.
  - The process is reproducible, observable, and ready for further AI-driven orchestration.

## 🛠️ Troubleshooting: Docker Compose Volume Masking System Binaries

### Problem
- When mounting the project root (e.g., `- .:/code`) in a Docker Compose service, system binaries like `git` may appear missing inside the container, even if they are present in the image.
- Symptom: `git: command not found` or `ls: cannot access '/usr/bin/git': No such file or directory` when running `which git` or `git --version` inside the container.

### Solution
1. **Force a full, no-cache rebuild of the image:**
   ```bash
   docker compose build --no-cache ollama-functions
   ```
2. **Test the container with and without volume mounts:**
   - Remove all `volumes:` from the service and check for system binaries.
   - If binaries are present, add back only the necessary mounts.
   - If you must mount the project root, always verify that system binaries are still accessible.
3. **Verify inside the container:**
   ```bash
   docker compose run --rm ollama-functions bash
   which git
   git --version
   ```

### Best Practice
- When troubleshooting missing binaries in Docker Compose containers, always check for volume masking and rebuild images with `--no-cache` if needed.

## Multi-Database Alembic Migration for memorydb

> **New Best Practice (2025-05-18):**
> We now use a dedicated Alembic environment for memorydb migrations. This ensures clean, isolated schema management for both rulesdb and memorydb.

### How it works
- A separate migrations directory (`migrations_memorydb/`) and config file (`alembic_memorydb.ini`) are used for memorydb.
- Migration scripts for memorydb are placed in `migrations_memorydb/versions/`.
- The Alembic config for memorydb points to the correct database and script location.
- Migrations are applied using:
  ```bash
  docker compose exec api alembic -c alembic_memorydb.ini upgrade head
  # or via Makefile:
  make -f Makefile.ai ai-memorydb-migrate
  ```
- Only keep memorydb-specific migrations in `migrations_memorydb/versions/` to avoid multiple heads.

### Example Workflow
1. Create or update migration scripts in `migrations_memorydb/versions/`.
2. Apply migrations:
   ```bash
   make -f Makefile.ai ai-memorydb-migrate
   ```
3. Verify tables in memorydb:
   ```bash
   docker compose exec db-test psql -U postgres -d memorydb -c "\\dt" | cat
   ```

### Best Practices
- Always pipe psql output to `cat` in automation to avoid prompt issues.
- Keep migration histories for each DB isolated.
- Document any manual steps or custom SQL in migration scripts. 
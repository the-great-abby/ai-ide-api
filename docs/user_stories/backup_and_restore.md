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
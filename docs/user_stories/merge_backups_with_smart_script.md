# User Story: Merging Multiple Postgres Backups with Smart Script and Makefile

## Motivation
As a developer or system administrator, I want to efficiently and safely merge data from multiple Postgres backup SQL files (from previous iterations or environments) into the current live database, so that I can recover, deduplicate, and update data without manual SQL or risk of data loss. This process should be repeatable, automated, and documented for future use.

## Actors
- Developer
- System Administrator

## Preconditions
- The project uses Docker Compose for service orchestration.
- The `smart_merge_backup.py` script exists at the project root and is up to date.
- All backup `.sql` files are located in the `backups/` directory at the project root.
- The Makefile.ai contains the `ai-smart-merge-backup` and `ai-smart-merge-all-backups` targets.
- The `misc-scripts` Docker Compose service is available and has access to the project code and backups.
- Environment variables for Postgres connection are set (PGUSER, PGPASSWORD, PGHOST, PGPORT, PGDATABASE).

## Step-by-Step Actions

### One-off Merge (Single File)
1. Place the backup SQL file in the `backups/` directory.
2. Ensure the `misc-scripts` service is running:
   ```bash
   make -f Makefile.ai ai-misc-up
   ```
3. From the project root, run:
   ```bash
   make -f Makefile.ai ai-smart-merge-backup BACKUP=backups/your_backup.sql
   ```
   - This runs the smart merge script, which restores the backup into a temp DB, detects tables, and upserts data into the live DB.

### Batch Merge (All Files)
1. Ensure all desired backup `.sql` files are in the `backups/` directory.
2. Ensure the `misc-scripts` service is running:
   ```bash
   make -f Makefile.ai ai-misc-up
   ```
3. From the project root, run:
   ```bash
   make -f Makefile.ai ai-smart-merge-all-backups
   ```
   - This loops over all `.sql` files in `backups/`, running the merge for each file in order.
   - Each file is processed in isolation, with logs for each step.

### Dry Run (Preview Actions)
1. To preview what would happen without making changes, run:
   ```bash
   make -f Makefile.ai ai-smart-merge-all-backups-dryrun
   ```
   - This prints the actions and SQL that would be run, without modifying the database.

## Expected Outcomes
- All data from the backup files is merged into the live database, with upserts (no duplicates, existing rows updated).
- The process is logged and repeatable.
- No manual SQL or direct DB manipulation is required.
- The workflow is robust to missing tables or schema changes (as long as columns match).

## Best Practices
- Always back up the current database before merging.
- Use the dry run mode to preview changes, especially after schema updates.
- Keep the `smart_merge_backup.py` script and Makefile.ai targets up to date with schema changes.
- Store this user story in `docs/user_stories/` and reference it in onboarding and code reviews.
- Prefer running merges in a controlled environment (e.g., staging) before production.

## References
- `smart_merge_backup.py` at project root
- `Makefile.ai` targets: `ai-smart-merge-backup`, `ai-smart-merge-all-backups`, `ai-smart-merge-all-backups-dryrun`
- `backups/` directory for SQL files
- Docker Compose service: `misc-scripts`

## Script Robustness and Safety

- The merge script now automatically skips upserts for:
  - Tables not present in the live database (as base tables in the public schema)
  - Tables with columns that do not match the live DB schema
  - Tables that cannot be imported via FDW (e.g., due to custom types, schema drift, or missing in the backup)
- The script logs every decision (skipped tables, mismatches, successful upserts) for full transparency.
- This makes the process resilient to schema drift, missing tables, and evolving database structure.

> **Best Practice:**
> You can safely run the batch merge on a directory of backups. Only compatible and safe data will be merged; all other cases are logged and skipped. 
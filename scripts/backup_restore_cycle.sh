#!/bin/bash
set -euo pipefail

# This script runs the destructive backup/restore cycle for rulesdb and memorydb.
# Run this from the project root on the host (not inside a container).
# It will:
#   1. Backup both databases (data-only)
#   2. Nuke the databases
#   3. Bring up API and DB, run migrations
#   4. Restore both databases (data-only)
#
# After running this script, re-run the Python test to verify data integrity.

# 1. Backup both databases (data-only)
echo "[backup_restore_cycle] Backing up rulesdb and memorydb (data-only)..."
make -f Makefile.ai ai-db-backup-data-only
make -f Makefile.ai ai-memorydb-backup-data-only

# Find latest backup files
echo "[backup_restore_cycle] Locating latest backup files..."
rules_backup=$(ls -t backups/rulesdb-data-*.sql | head -1)
memory_backup=$(ls -t backups/memorydb-data-*.sql | head -1)
echo "  rulesdb:   $rules_backup"
echo "  memorydb:  $memory_backup"

# 2. Nuke both databases
echo "[backup_restore_cycle] Nuking databases..."
make -f Makefile.ai ai-db-nuke

# 3. Bring up API and DB, run migrations
echo "[backup_restore_cycle] Bringing up API/DB and running migrations..."
make -f Makefile.ai ai-up
make -f Makefile.ai ai-api-wait
make -f Makefile.ai ai-db-migrate

# 4. Restore both databases (data-only)
echo "[backup_restore_cycle] Restoring rulesdb and memorydb (data-only)..."
make -f Makefile.ai ai-db-restore-data BACKUP=$rules_backup
make -f Makefile.ai ai-memorydb-restore-data BACKUP_FILE=$memory_backup

echo "[backup_restore_cycle] Backup/restore cycle complete. Now re-run the Python test to verify data integrity." 
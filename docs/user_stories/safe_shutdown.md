# User Story: Safe Shutdown — Back Up and Stop All Services Before Powering Down

## Motivation
As a developer, maintainer, or system administrator, I want a simple, reliable workflow to safely shut down the system—ensuring all critical data is backed up and all services are gracefully stopped—so that I can power down my computer or environment without risk of data loss.

---

## Actors
- Developer
- System Administrator
- Anyone powering down the system or environment

---

## Preconditions
- Docker, Docker Compose, and `Makefile.ai` are available.
- The system is running and you want to preserve the current state/data.

---

## Step-by-Step Actions

### 1. Back Up All Critical Data
- **Back up rulesdb (data only):**
  ```bash
  make -f Makefile.ai ai-db-backup-data-only
  # Backup is saved in backups/rulesdb-data-YYYYMMDD-HHMMSS.sql
  ```
- **Back up memorydb (data only):**
  ```bash
  make -f Makefile.ai ai-memorydb-backup-data-only
  # Backup is saved in backups/memorydb-data-YYYYMMDD-HHMMSS.sql
  ```
- **(Optional) Full backup (schema + data for both DBs):**
  ```bash
  make -f Makefile.ai ai-db-backup-all
  # Backups are saved in backups/ with timestamps
  ```

### 2. (Optional) Verify Backups
- Check that the backup files exist in the `backups/` directory and have recent timestamps.
- (Optional) Open the files to confirm they contain SQL dump data.

### 3. Gracefully Stop All Services
- **Preferred:**
  ```bash
  make -f Makefile.ai ai-down
  # Or, if not available:
  docker compose down
  ```
- **(Optional) For a full clean, remove volumes:**
  ```bash
  docker compose down -v
  # WARNING: This will delete all database and service volumes!
  ```

---

## Expected Outcomes
- All important data is safely backed up in the `backups/` directory.
- All containers and services are stopped cleanly.
- The system can be safely powered down or restarted later without risk of data loss.

---

## Best Practices
- **Always run this workflow before shutting down your computer or environment, especially if you have made changes you want to keep.**
- Store backup files in a location that is regularly backed up (e.g., cloud storage, external drive) for extra safety.
- Periodically test restoring from backups to ensure they are valid.
- Document this workflow in onboarding and admin guides.

---

## Troubleshooting
- If a backup command fails, check that the database containers are running (`make -f Makefile.ai ai-up` or `docker compose ps`).
- If you see permission errors, ensure you have write access to the `backups/` directory.
- If you need to restore data, see the [backup_and_restore.md](backup_and_restore.md) user story for detailed restore steps.

---

## References
- Makefile.ai targets: `ai-db-backup-data-only`, `ai-memorydb-backup-data-only`, `ai-db-backup-all`, `ai-down`
- [backup_and_restore.md](backup_and_restore.md)
- [db_schema_recovery_and_data_restore.md](db_schema_recovery_and_data_restore.md)
- [system_rebuild_and_restart.md](system_rebuild_and_restart.md) 
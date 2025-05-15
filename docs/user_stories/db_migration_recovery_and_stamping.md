# User Story: Database Migration Recovery & Alembic Stamping

## Motivation
As a developer or admin, I want to quickly recover from Alembic migration mismatches or missing revision errors, so that I can keep the database and migration history in sync and continue development without downtime.

## Actors
- **Developer/Admin:** Maintains the database and migration history.
- **Docker Compose Services:** Provide a reproducible environment for migrations.

## Preconditions
- The database and Alembic migration history are out of sync (e.g., after a failed migration, missing file, or manual DB change).
- You see errors like `Can't locate revision identified by ...` when running Alembic commands.

## Steps (Recovery Flow)
1. **Stamp the database to the current Alembic head:**
   - Command:
     ```bash
     make -f Makefile.ai ai-db-stamp-head
     ```
   - This marks the database as being at the latest migration, without running migrations.

2. **Re-run migration autogeneration:**
   - Command:
     ```bash
     make -f Makefile.ai ai-db-autorevision
     ```

3. **Apply the new migration:**
   - Command:
     ```bash
     make -f Makefile.ai ai-db-migrate
     ```

4. **Verify:**
   - Ensure the database and migration history are now in sync.
   - Run your app/tests to confirm.

## Expected Outcomes
- The database is marked as up-to-date with the latest migration.
- New migrations can be generated and applied without errors.
- Development can continue without downtime.

## Best Practices
- Always use Makefile targets for migration management.
- Avoid manual DB changes outside of migrations.
- Keep migration files under version control.
- Document any manual recovery steps in the user stories or onboarding docs.

## References
- Makefile.ai targets: `ai-db-stamp-head`, `ai-db-autorevision`, `ai-db-migrate`
- Typical error: `Can't locate revision identified by ...` 
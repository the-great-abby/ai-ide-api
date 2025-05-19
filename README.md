# Backup Merge Automation

For robust, repeatable merging of multiple Postgres backup SQL files into your live database, this project provides:
- A smart merge script (`smart_merge_backup.py`)
- Makefile.ai targets for single and batch merges (with Docker Compose integration)
- A documented workflow and best practices

**See the full user story and step-by-step guide:**
[docs/user_stories/merge_backups_with_smart_script.md](docs/user_stories/merge_backups_with_smart_script.md)

---

## Recent Enhancements

### Rule Proposal Feedback Loop

- **Endpoints:**
  - `POST /api/rule_proposals/{proposal_id}/feedback` — Submit anonymous feedback (accept, reject, needs_changes, comments).
  - `GET /api/rule_proposals/{proposal_id}/feedback` — List all feedback for a proposal.
- **Purpose:** Enables users to provide feedback on rule proposals, supporting continuous improvement and community-driven rule curation.

### Database Model

- **Table:** `rule_proposal_feedback`
  - Fields: `id`, `rule_proposal_id`, `feedback_type`, `comments`, `created_at`
- **Migration:** Managed via Alembic, auto-discovered by importing the model in `migrations/env.py`.

### Makefile Enhancements

- **`api-up` target:** Starts both API and database containers.
- **Pre-commit Docker integration:** Run code quality checks in a containerized environment.

### Testing & Data Management

- **Backup:** `make -f Makefile.ai ai-db-backup`
- **Restore:** `make -f Makefile.ai ai-db-restore-data BACKUP=backups/yourfile.sql`
- **Schema reset:** `make -f Makefile.ai ai-db-nuke` and `make -f Makefile.ai ai-db-migrate`

---

For more details, see the relevant sections in this documentation. 
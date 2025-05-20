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

# Portable AI-Powered Memory Logging & Git Diff Summarization

Easily enable automated memory logging and LLM-powered git diff summarization in any project!

## Quick Start
```bash
# Copy scripts and Makefile.memory from a reference repo
cp -r ../ai-ide-api/scripts ./scripts
cp ../ai-ide-api/Makefile.memory ./Makefile.memory

# (Optional) Set environment variables
export PROJECT=my-other-repo
export MEMORY_API_URL=http://shared-server:9103/memory/nodes

# Log a git diff as a memory node
make -f Makefile.memory ai-memory-log-git-diff
```

## Setup Steps
1. Copy or symlink `scripts/` and `Makefile.memory` into your repo.
2. Set environment variables as needed (`PROJECT`, `NAMESPACE`, `MEMORY_API_URL`, `LLM_API_URL`, `DIFFS_DIR`).
3. Start or connect to the required services (Memory API, LLM Summarization API).
4. Run the workflow with `make -f Makefile.memory ai-memory-log-git-diff`.

## Best Practices
- Use environment variables for all project-specific values
- Namespace memory nodes by project for easy filtering
- Store only references to large diffs, not the full content
- Use `.env` files for local overrides
- Reference the [portable memory logging user story](docs/user_stories/portable_memory_logging_onboarding.md) for full onboarding and advanced usage

---

For more details, see [docs/user_stories/portable_memory_logging_onboarding.md](docs/user_stories/portable_memory_logging_onboarding.md) 
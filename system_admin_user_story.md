# User Story: System Admin — Managing the AI-Augmented Code Review System

## Overview
This user story describes the responsibilities and daily/weekly workflow of a system administrator managing the AI-augmented code review and rule proposal system. It includes the key Makefile.ai commands and best practices for setup, maintenance, and troubleshooting.

---

## Actors
- **System Admin:** Responsible for environment setup, service orchestration, database management, and troubleshooting.
- **Developers/AI Users:** Rely on the system being available, up-to-date, and consistent.

---

## Key Responsibilities
- Launch and monitor all required services (API, DB, frontend, etc.)
- Manage database migrations, backups, and restores
- Ensure environment consistency (Docker, Makefile.ai)
- Troubleshoot and resolve system issues
- Support onboarding of new users and AIs

---

## End-to-End System Admin Workflow

### 1. Environment Setup
- Build and start all services:
  ```bash
  docker compose build
  docker compose up -d
  # or, preferred:
  make -f Makefile.ai ai-up-test  # Starts test containers
  make -f Makefile.ai ai-api-wait # Waits for API to be ready
  ```

### 2. Database Migration & Initialization
- Apply all migrations:
  ```bash
  make -f Makefile.ai ai-db-migrate
  ```
- If there are migration conflicts (multiple heads):
  ```bash
  make -f Makefile.ai ai-db-merge-heads
  make -f Makefile.ai ai-db-stamp-head
  make -f Makefile.ai ai-db-migrate
  ```

### 3. Data Management
- Backup the database:
  ```bash
  make -f Makefile.ai ai-db-backup
  # Data-only backup:
  make -f Makefile.ai ai-db-backup-data-only
  ```
- Restore from backup:
  ```bash
  make -f Makefile.ai ai-db-restore BACKUP=backups/yourfile.sql
  # Data-only restore:
  make -f Makefile.ai ai-db-restore-data BACKUP=backups/yourfile.sql
  ```
- Nuke and reset the database (dangerous!):
  ```bash
  make -f Makefile.ai ai-db-nuke
  make -f Makefile.ai ai-db-migrate
  ```

### 4. Ollama LLM API & Functions Service
- **Build and run the Ollama-powered LLM functions service:**
  ```bash
  make -f Makefile.ai ai-build-ollama-functions-service
  make -f Makefile.ai ai-run-ollama-functions-service
  # This will build and run the FastAPI service for LLM-powered rule suggestions.
  # The service will be available on port 8000 by default.
  ```
- **Start the Ollama backend (if not already running):**
  ```bash
  make -f Makefile.ai ai-ollama-serve-docker-gateway
  # or, to run in the background:
  make -f Makefile.ai ai-ollama-serve-docker-gateway-bg
  # Logs can be viewed with:
  make -f Makefile.ai ai-ollama-logs
  ```
- **Restart or kill Ollama backend:**
  ```bash
  make -f Makefile.ai ai-ollama-restart-docker-gateway
  make -f Makefile.ai ai-ollama-kill
  ```
- **Environment variables:**
  - `OLLAMA_URL` (default: http://host.docker.internal:11434/api/generate)
  - `OLLAMA_MODEL` (set to specify a particular LLM model)

### 5. Service Management
- Restart API or other containers:
  ```bash
  make -f Makefile.ai ai-api-restart-wait
  docker compose restart <service>
  ```
- Stop all containers:
  ```bash
  docker compose down
  ```

### 6. Testing & Validation
- Run all tests (always use Makefile.ai targets):
  ```bash
  make -f Makefile.ai ai-test PYTEST_ARGS="-x"
  make -f Makefile.ai ai-test-unit PYTEST_ARGS="-x"
  make -f Makefile.ai ai-test-integration PYTEST_ARGS="-x"
  ```
- Clean up test environment:
  ```bash
  make -f Makefile.ai ai-test-clean
  ```

### 7. Monitoring & Troubleshooting
- Check logs:
  ```bash
  docker compose logs <service>
  tail -f ollama.log  # For Ollama LLM service
  ```
- Inspect DB state:
  ```bash
  make -f Makefile.ai ai-db-heads
  make -f Makefile.ai ai-db-history
  ```
- Rollback failed DB transactions:
  ```bash
  make -f Makefile.ai ai-db-rollback
  ```

---

## Best Practices
- **Always use Makefile.ai** for all operations to ensure environment consistency.
- **Document all changes** to the environment, migrations, and backups.
- **Automate regular backups** and test restores.
- **Keep onboarding docs up to date** for new users and AIs.
- **Monitor logs and system health** regularly.

---

## Example Weekly Admin Checklist
1. Pull latest code and Makefile.ai updates.
2. Rebuild and restart all services.
3. Apply any new migrations.
4. Run and verify all tests.
5. Backup the database.
6. Review logs and system health.
7. Onboard any new users or AIs.

---

## Goal
By following this workflow, the system admin ensures the platform is reliable, up-to-date, and ready for both human and AI users to collaborate and improve code quality. 
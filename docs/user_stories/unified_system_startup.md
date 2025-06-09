# User Story: Unified System & LLM Startup After Restart or Onboarding

## Motivation
As a developer, maintainer, or new team member, I want a single, unified workflow to bring the entire system—including core services, Ollama LLM backend, and the Ollama gateway—online after a restart or for onboarding, so that I can reliably get all features running with minimal manual steps.

---

## Actors
- Developer
- System Administrator
- CI/CD Pipeline
- New team member (onboarding)

---

## Preconditions
- Docker, Docker Compose, and `Makefile.ai` are available.
- Ollama is installed (if running on host) and the required model is available.
- The `ollama-functions` gateway service is defined in `docker-compose.yml`.
- Code, dependencies, or models may have changed, or the system is being started after a shutdown.

---

## Step-by-Step Actions

> **Note:**
> - If you are doing a fresh start (e.g., onboarding, new environment, or you do not need to preserve existing data), you can skip the database backup step below.
> - Only perform the backup if you want to preserve the current database state before making changes or restarting services.

### 1. (Optional) Back Up Database Data (Skip for Fresh Start)
```bash
make -f Makefile.ai ai-db-backup-data-only
# Backup is saved in backups/rulesdb-data-YYYYMMDD-HHMMSS.sql
```

### 2. Rebuild All Docker Images (if code or dependencies changed)
```bash
make -f Makefile.ai ai-rebuild-all
# Optionally, add NOCACHE=1 to force a no-cache build
```

### 3. Pull the Required Ollama Model (if using LLM features)
```bash
make -f Makefile.ai ai-ollama-pull-model
```

### 4. Start the Ollama Backend (Host, in Background)
```bash
make -f Makefile.ai ai-ollama-serve-docker-gateway-bg
```

### 5. Start All Core Services (API, DB, Frontend, etc.)
```bash
make -f Makefile.ai ai-up
```

### 6. Start the Ollama Gateway Service (Docker Compose)
```bash
make -f Makefile.ai ai-up-ollama-functions
```

### 7. Run Database Migrations (if needed)
```bash
make -f Makefile.ai ai-db-migrate
```

### 8. Verify All Services Are Running and Healthy
```bash
make -f Makefile.ai ai-status
make -f Makefile.ai ai-ollama-functions-health
make -f Makefile.ai logs-api
make -f Makefile.ai logs-admin-frontend
make -f Makefile.ai logs-frontend
make -f Makefile.ai ai-ollama-functions-logs
```

---

## Docker Compose Profiles, Environment Management, and Safe Edits

To make onboarding, development, and testing smoother, we use Docker Compose **profiles** and per-service environment files. This allows you to:
- Start only the services you need (e.g., core dev, LLM, test, or worker-only)
- Use the correct environment variables for each service and context
- Avoid accidental misconfiguration or resource waste

### Profiles in Compose
- `dev`: Core API, DB, Redis, etc.
- `llm`: LLM worker, Ollama, and related services
- `test`: Test API, test DB, test Redis, etc.
- `llm-test`: LLM worker in test mode

### Example: Starting Services by Profile
```bash
# Core development
make dev-up
# LLM/AI features
make llm-up
# API testing
make test-up
# LLM worker test mode
make llm-test-up
# Stop all
make down
```

### Environment Management
- Each service/worker has a template env file: `change-this-env.<service>.example`
- Copy and edit these as needed (e.g., `cp change-this-env.llm-worker.example .env.llm-worker`)
- Reference these files in your Compose service definitions using `env_file:`

### Safe Editing: Always Back Up Compose Files
Before making changes to `docker-compose.yml` or `docker-compose.test.yml`, create a timestamped backup:
```bash
cp docker-compose.yml docker-compose.yml.bak.$(date +%Y%m%d-%H%M%S)
cp docker-compose.test.yml docker-compose.test.yml.bak.$(date +%Y%m%d-%H%M%S)
```

### Best Practices
- Only start the services you need for your workflow
- Use the correct env file for each service/profile
- Never mix dev and test settings in the same env file
- Document new profiles/env files as you add them
- Always make a backup before editing Compose files

---

## Expected Outcomes
- All core services, Ollama backend, and gateway are running and healthy.
- The system is ready for LLM-powered features and normal operation.
- The process is standardized, easy to follow, and minimizes manual troubleshooting.

---

## Best Practices
- **Always back up your data before destructive operations if you want to preserve it.**
- Use the no-cache option if you suspect Docker cache issues.
- Check Ollama gateway health before running LLM-dependent features or tests.
- Automate this setup in onboarding scripts or CI/CD pipelines if possible.
- Document any issues or troubleshooting steps for future reference.

---

## Troubleshooting
- If changes are not reflected, try a no-cache rebuild:
  ```bash
  make -f Makefile.ai ai-rebuild-all NOCACHE=1
  ```
- If containers fail to start, check logs and ensure all dependencies are installed.
- For persistent issues, try a full clean:
  ```bash
  docker compose down -v
  make -f Makefile.ai ai-db-backup-data-only
  make -f Makefile.ai ai-rebuild-all NOCACHE=1
  make -f Makefile.ai ai-up
  ```
- If Ollama gateway health check fails, ensure both backend and gateway are running:
  ```bash
  make -f Makefile.ai ai-ollama-serve-docker-gateway-bg
  make -f Makefile.ai ai-up-ollama-functions
  make -f Makefile.ai ai-ollama-functions-health
  ```
- If model not found or outdated, pull or update the model:
  ```bash
  make -f Makefile.ai ai-ollama-pull-model
  ```
- For logs and debugging:
  ```bash
  make -f Makefile.ai ai-ollama-functions-logs
  make -f Makefile.ai ai-ollama-logs
  ```

---

## References
- Makefile.ai targets: `ai-db-backup-data-only`, `ai-rebuild-all`, `ai-up`, `ai-db-migrate`, `ai-status`, `logs-api`, `logs-admin-frontend`, `logs-frontend`, `ai-ollama-pull-model`, `ai-ollama-serve-docker-gateway-bg`, `ai-up-ollama-functions`, `ai-ollama-functions-health`, `ai-ollama-functions-logs`, `ai-ollama-kill`, `ai-restart-ollama-functions`, `ai-ollama-restart-docker-gateway`
- [system_rebuild_and_restart.md](system_rebuild_and_restart.md)
- [ollama_gateway_support.md](ollama_gateway_support.md)
- [llm_onboarding.md](llm_onboarding.md) 
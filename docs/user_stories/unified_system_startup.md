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

## (Optional) Restart or Kill Ollama Services
- **Kill Ollama backend:**
  ```bash
  make -f Makefile.ai ai-ollama-kill
  ```
- **Restart Ollama gateway:**
  ```bash
  make -f Makefile.ai ai-restart-ollama-functions
  ```
- **Restart Ollama backend:**
  ```bash
  make -f Makefile.ai ai-ollama-restart-docker-gateway
  ```

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
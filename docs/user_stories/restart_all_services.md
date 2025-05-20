# User Story: Restarting All Core Services Without Full Rebuild or Shutdown

## Motivation
As a developer, maintainer, or system administrator, I want a single, unified command to restart all core services (API, Ollama functions, frontend, misc-scripts) without performing a full rebuild or shutting down the database, so that I can quickly refresh the system after configuration changes, memory leaks, or for troubleshooting, with minimal manual steps.

## Actors
- Developer
- System Administrator
- CI/CD Pipeline

## Preconditions
- Docker, Docker Compose, and `Makefile.ai` are available.
- All core services are already running or have been started at least once.
- You do **not** want to restart the database (for that, see full rebuild or shutdown stories).

## Step-by-Step Actions

### 1. Restart All Core Services
Use the new Makefile target:
```bash
make -f Makefile.ai ai-restart-all
```
This will:
- Restart the API service
- Restart the Ollama functions service
- Restart the Ollama backend (now in the background, AI/automation-friendly)
- Restart the frontend service
- Restart the misc-scripts service

**Note:**
- The database (`db-test`) is **not** restarted by this command.
- The Ollama backend is restarted in the background using `ai-ollama-restart-docker-gateway-bg`, which avoids blocking the Makefile and is preferred for AI/automation workflows.
- This command is safe to run while the system is live; it will briefly stop and start each service container.
- If you need to restart the database, see [system_rebuild_and_restart.md](system_rebuild_and_restart.md) or [safe_shutdown.md](safe_shutdown.md).

### 2. Verify Services Are Running
After running the restart command, check service status and logs:
```bash
make -f Makefile.ai ai-status
make -f Makefile.ai logs-api
make -f Makefile.ai logs-admin-frontend
make -f Makefile.ai logs-frontend
```

## Expected Outcomes
- All core services are restarted and running the latest code/configuration present in their containers.
- The process is fast and does not interrupt the database or persistent data.
- Developers and admins have a single, easy-to-remember command for service refresh.

## Best Practices
- Use this workflow after config changes, memory leaks, or to clear stuck processes.
- For code or dependency changes, use the full rebuild workflow ([system_rebuild_and_restart.md](system_rebuild_and_restart.md)).
- For safe shutdowns or database restarts, see [safe_shutdown.md](safe_shutdown.md).
- Document any issues or troubleshooting steps for future reference.

## Troubleshooting
- If a service fails to restart, check its logs for errors.
- If changes are not reflected, ensure you did not need a full rebuild (`ai-rebuild-all`) or a no-cache build.
- If you need to restart the database, use the appropriate Makefile target or see the related user stories below.

## References
- Makefile.ai target: `ai-restart-all`
- Related user stories:
  - [System Rebuild and Restart After Code or Dependency Changes](system_rebuild_and_restart.md)
  - [Safe Shutdown — Back Up and Stop All Services Before Powering Down](safe_shutdown.md)
  - [Rebuilding and Reloading the Frontend via Makefile](frontend_rebuild_and_reload.md) 
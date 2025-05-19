# User Story: System Rebuild and Restart After Code or Dependency Changes

## Table of Contents

1. [Motivation](#motivation)
2. [Actors](#actors)
3. [Preconditions](#preconditions)
4. [Step-by-Step Actions](#step-by-step-actions)
    - [1. Back up database data only](#1-back-up-database-data-only)
    - [2. Rebuild all Docker images](#2-rebuild-all-docker-images)
    - [3. Restart all services](#3-restart-all-services)
    - [4. Run database migrations (if needed)](#4-run-database-migrations-if-needed)
    - [5. Verify all services are running and healthy](#5-verify-all-services-are-running-and-healthy)
5. [Expected Outcomes](#expected-outcomes)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [References](#references)

## Motivation
As a developer or maintainer, I want a single, unified workflow to rebuild and restart all services after code or dependency changes, so that the system is always running the latest code and dependencies with minimal manual steps.

## Actors
- Developer
- CI/CD system
- Project maintainer

## Preconditions
- Code or dependencies have changed (backend, frontend, scripts, Dockerfiles, requirements, etc.).
- Docker Compose and `Makefile.ai` are available in the project.

## Step-by-Step Actions

### 1. Back up database data only
(ALWAYS do this before stopping or rebuilding containers):
```bash
make -f Makefile.ai ai-db-backup-data-only
# Backup is saved in backups/rulesdb-data-YYYYMMDD-HHMMSS.sql
```

### 2. Rebuild all Docker images
```bash
make -f Makefile.ai ai-rebuild-all
```
- (Optionally, add `NOCACHE=1` to force a no-cache build.)

### 3. Restart all services
```bash
make -f Makefile.ai ai-up
```

### 4. Run database migrations (if needed)
```bash
make -f Makefile.ai ai-db-migrate
```

### 5. Verify all services are running and healthy
Use logs and status targets:
```bash
make -f Makefile.ai ai-status
make -f Makefile.ai logs-api
make -f Makefile.ai logs-admin-frontend
make -f Makefile.ai logs-frontend
```

## Expected Outcomes
- All services are running the latest code and dependencies.
- The process is standardized and easy to remember.
- No manual Docker or Compose commands are needed.
- Data is safely backed up before any destructive operation.

## Best Practices
- **Always back up your data (data-only) before stopping or rebuilding containers.**
- Use this workflow after any code or dependency change.
- Use the no-cache option if you suspect Docker cache issues.
- Document any issues or troubleshooting steps for future reference.
- Reference this user story in onboarding and developer docs.

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

## References
- Makefile.ai targets: `ai-db-backup-data-only`, `ai-rebuild-all`, `ai-up`, `ai-db-migrate`, `ai-status`, `logs-api`, `logs-admin-frontend`, `logs-frontend`
- [ONBOARDING.md](../ONBOARDING.md) 
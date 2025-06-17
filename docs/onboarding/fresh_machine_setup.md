# Fresh Machine Setup Guide for ai-ide-api

This guide will help you get the project up and running on a new Mac or Linux machine using only Makefile and Docker-based commands. No manual Python or Node setup required—let the Makefiles and Docker do the heavy lifting!

---

## 1. Install Prerequisites
- **Docker Desktop**: [Download and install](https://www.docker.com/products/docker-desktop/)
- **Make**: Usually pre-installed. Check with:
  ```bash
  make --version
  ```
  If missing, install via your system's package manager (e.g., `xcode-select --install` on Mac, `sudo apt install make` on Ubuntu).

---

## 2. Start the Test Environment
```bash
make -f Makefile.ai ai-up-test
```
Brings up all required Docker containers for the test environment.

---

## 3. Initialize/Reset the Test Database
```bash
make -f Makefile.ai test-setup
```
Drops, recreates, and initializes the test database and ensures all services are ready.

---

## 4. Run MemoryDB Migrations (if applicable)
If your workflow or features require the memorydb, run its migrations as well:
```bash
make -f Makefile.ai-db ai-memorydb-migrate
```
This ensures the memorydb schema is up to date.

---

## 5. Run Backend Tests
```bash
make -f Makefile.ai ai-test
# Or, for specific test types:
make -f Makefile.ai ai-test-unit
make -f Makefile.ai ai-test-integration
```

---

## 6. Run the Test Frontend (Admin)

There is currently **no Makefile target** for starting the test frontend directly. To start the test frontend, use Docker Compose:

```bash
docker compose -f docker-compose.test.yml up -d test-frontend
```

> **Recommendation:** For convenience, add a Makefile target (e.g., `test-frontend-up`) to automate this step:
> ```makefile
> test-frontend-up:
> 	docker compose -f docker-compose.test.yml up -d test-frontend
> ```

Once started, access the test frontend in your browser (typically at http://localhost:9104 or as specified in your docker-compose.test.yml).

---

## 7. Miscellaneous
- Ensure the dev misc-scripts Docker container is running for commits/project map automation.
- Check onboarding docs in `docs/onboarding/` or `ONBOARDING.md` for any project-specific steps or updates.

---

## Summary Table

| Step | Command/Action | Notes |
|------|---------------|-------|
| 1    | Install Docker Desktop, ensure Make is available | Prerequisites |
| 2    | `make -f Makefile.ai ai-up-test` | Start Docker test environment |
| 3    | `make -f Makefile.ai test-setup` | Initialize/reset test DB |
| 4    | `make -f Makefile.ai-db ai-memorydb-migrate` | Migrate memorydb schema |
| 5    | `make -f Makefile.ai ai-test` | Run backend tests |
| 6    | `docker compose -f docker-compose.test.yml up -d test-frontend` | Run test frontend |
| 7    | Check docs/onboarding/ | Project-specific steps |

---

If you encounter issues or need a more tailored workflow, check the other onboarding docs or ask Quartermaster "Patch" McDebug for help! 
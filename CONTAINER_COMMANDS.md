# Container Command Mapping

This document lists which commands and tools should be run in which containers for development, testing, and operations.

| Command/Tool | Container/Service | Notes |
|--------------|------------------|-------|
| `alembic`    | `api`            | Run all Alembic migrations and migration status commands here. |
| `psql`       | `test-db` (test), `db` (dev)        | Use for direct database inspection, manual SQL, and schema checks. |
| `pytest`     | `backend-test` (or via Makefile.ai) | All test runs should use Makefile.ai targets, which run in the correct environment. |
| `pre-commit` | Host or `pre-commit` container | For linting and code checks. |
| `scripts/*`  | Varies           | See script header or Makefile target for correct context. |

## Best Practices
- Always use the documented container for each command to avoid environment mismatches.
- If you add a new tool, script, or workflow, **add it to this list** and update onboarding docs as needed.
- Reference this file in code reviews and onboarding.

## Rule for Growing This List
- Whenever a new command, tool, or workflow is introduced that requires a specific container or context, update this file.
- If you find yourself or others running a command in the wrong place, add a clarifying entry here.
- Review this file periodically for accuracy and completeness.

## Enforcing Correct Execution Context

To prevent accidental execution in the wrong environment, use the helper script:

    scripts/check_container_context.py

- **How to use:**
    - Import or call this script at the top of any script that must only run inside a specific container (e.g., API, test, misc-scripts).
    - The script will refuse to run and print a clear error if not inside the correct Docker container (checks for RUNNING_IN_DOCKER=1 or /.dockerenv).
    - This helps enforce best practices and avoids environment mismatches.

**Best Practice:**
- All new scripts and command-line tools should use this check.
- Reference this script in onboarding and code review for new workflows. 


Add this to your .zshrc
    alias pytest='echo "[ERROR] Use make -f Makefile.ai ai-test" && exit 1'
    alias alembic='echo "[ERROR] Use make -f Makefile.ai ai-db-migrate" && exit 1'

## Docker Postgres Service Names

| Environment | Service Name |
|-------------|--------------|
| Dev/Prod    | db           |
| Test/CI     | test-db      |

> **Note:** All general usage, onboarding, and code samples use `db` as the default Postgres service/container. Use `test-db` only for test/CI environments or when running tests.
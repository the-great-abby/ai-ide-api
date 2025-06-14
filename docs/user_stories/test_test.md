# User Story: test (and test-test)

## Motivation
Ensure all contributors and CI systems can reliably run the full test suite in a standardized, containerized environment using the new Makefile.ai-test targets. This prevents environment drift, ensures consistency, and makes onboarding easier for new crew members.

## Actors
- Developers: Run the full test suite locally to verify changes before merging.
- CI/CD Systems: Execute the test suite automatically on every push or pull request.
- QA Engineers: Validate that the application passes all automated tests in a clean environment.

## Preconditions
- Docker and Docker Compose are installed and running.
- The test containers are built and available (if not, they will be built automatically).
- The workspace is at the project root.

## Why Nuke the Test DB?
To ensure a truly clean, modern test environment, always nuke (fully reset) the test database before running migrations and tests. This prevents issues with ghost tables, schema drift, or leftover data from previous runs. Nuking guarantees that migrations are applied to an empty database, so any missing tables or migration errors are caught early and reliably.

**Common issues prevented by nuking:**
- Missing tables (e.g., proposals) due to incomplete migrations
- Old schema artifacts causing test failures
- Data contamination from previous test runs

## Step-by-Step Actions: Clean Test Cycle
1. **Nuke the test database:**
   ```bash
   make -f Makefile.ai-test test-db-nuke
   ```
   (Removes all test DB containers, volumes, and data)
2. **Apply all migrations:**
   ```bash
   make -f Makefile.ai-test test-db-migrate
   ```
   (Ensures the schema is up to date from a clean slate)
3. **Run the full test suite:**
   ```bash
   make -f Makefile.ai-test test
   ```
   (Shortcut for `make -f Makefile.ai-test test-test`)
   
   Optionally, pass extra pytest arguments:
   ```bash
   make -f Makefile.ai-test test PYTEST_ARGS="-k <pattern>"
   ```

## All-in-One Workflow
For a one-command workflow that performs all the above steps (nuke, migrate, test), use:
```bash
make -f Makefile.ai-test test-quickstart
```
See [test-quickstart user story](test_quickstart.md) for details.

## Expected Outcomes
- All tests are executed in a clean, isolated Docker environment
- Results are displayed in the terminal, including any failures or errors
- The environment remains consistent across all contributors and CI runs

## Best Practices
- Always nuke the test DB before running migrations and tests for a clean slate
- Use the `test` target via `Makefile.ai-test` for running the full suite quickly
- `test-test` remains available for clarity or scripting
- Use `PYTEST_ARGS` to filter or customize test runs as needed
- Use `test-quickstart` for a full reset, migrate, and test cycle
- Clean up with `make -f Makefile.ai-test test-down` or `ai-test-cleanup` before/after major changes
- Document any additional test targets or workflows in user stories for discoverability
- Save test output for further analysis:
  ```bash
  make -f Makefile.ai-test test > test_output.txt
  ```

## Troubleshooting
- **Test failures:** Review the output for stack traces and error messages.
- **Old data or schema issues:** Ensure the test DB was nuked and migrations applied.
- **Containers not starting:** Check Docker status and logs for errors.
- **Environment drift:** Use test-quickstart to reset everything to a known state.

### Troubleshooting: Stubborn Volumes
If you nuke the test DB but still see old tables or data, the Docker volume may not have been fully removed. As a last resort, you can manually delete the test DB volume using the Docker Desktop UI (Volumes tab) or with the CLI:

```bash
docker volume ls  # Find the test DB volume name (e.g., rules_postgres_data_test_fresh...)
docker volume rm <volume_name>
```

After manual removal, rerun the nuke and start the test-db container to ensure a truly clean slate.

## Advanced: Forcing a Fresh Test DB Volume

Sometimes, Docker or the Makefile may reuse an old test DB volume even after running the nuke target. To guarantee a truly clean slate, you can manually specify a unique volume name using the `TEST_DB_VOLUME` environment variable:

```bash
TEST_DB_VOLUME=rules_postgres_data_test_fresh_$(date +%Y%m%d_%H%M%S) make -f Makefile.ai-test test-db-nuke
```

- This will force Docker to create and use a new, uniquely named volume for the test database.
- After running this, proceed with migrations and tests as usual.

**Why is this necessary?**
- Docker Compose may sometimes reuse a previous volume if the name is not changed, leading to stale data or schema.
- Manually setting `TEST_DB_VOLUME` ensures the nuke process truly wipes the slate clean, which is critical for debugging migration or schema issues.

Refer to this step if you ever see old tables or data after a nuke, or if migrations fail due to unexpected schema state.

# User Story: ai-test-cleanup

## Motivation
Ensure the test environment is completely reset between runs to prevent test flakiness, resource conflicts, and contamination from previous runs. This enables reliable, repeatable, and isolated test cycles for all contributors and CI systems.

## Actors
- Developers: Run tests locally and need a clean environment for accurate results.
- CI/CD Systems: Automatically clean up after test jobs to maintain a stable build pipeline.
- QA Engineers: Require consistent, isolated test environments for manual or automated testing.

## Preconditions
- The test or development environment has been used (containers, networks, or volumes may be running).
- There may be leftover __pycache__ directories or .pyc files from previous Python runs.

## Step-by-Step Actions
1. Run make ai-test-cleanup from the project root.
2. The target executes:
   - make down (stops and removes dev containers, networks, and volumes)
   - docker compose -f docker-compose.test.yml down (stops and removes test containers, networks, and volumes)
   - make clean-pycache (removes all __pycache__ directories and .pyc files)
3. All containers, networks, and volumes for both dev and test are stopped and removed.
4. All Python cache files are deleted.
5. The environment is now clean and ready for a fresh test or dev cycle.

## Expected Outcomes
- No running containers, networks, or volumes from previous test/dev runs.
- No leftover Python cache files.
- The next test or dev run starts from a known, clean state.
- Reduced risk of test flakiness or environment-related errors.

## Best Practices
- Run ai-test-cleanup before and after major test cycles, especially when switching branches or debugging environment issues.
- Integrate ai-test-cleanup into CI/CD pipelines to ensure clean builds.
- Use this target whenever you encounter unexplained test failures or environment conflicts.
- Document any additional cleanup steps needed for new services or dependencies.
- Save cleanup output for further analysis:
  ```bash
  make -f Makefile.ai-test ai-test-cleanup > cleanup_output.txt
  ```

## Troubleshooting
- **Containers not stopping:** Check the output for errors and ensure no dependent services are running.
- **Volumes not removed:** Verify that Docker has removed all test/dev volumes.
- **Leftover cache files:** Ensure the clean-pycache step completes successfully.
- **Environment not clean:** Double-check for running containers or volumes with `docker ps` and `docker volume ls`.

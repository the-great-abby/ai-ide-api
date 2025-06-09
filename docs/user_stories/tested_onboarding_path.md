# User Story: Accurate and Testable Onboarding Process

## Motivation
To ensure onboarding logic is robust, reliable, and future-proof, we maintain a dedicated onboarding path (`test_path`) in `onboarding_paths.json` that is exercised by automated tests. This guarantees that onboarding flows (including token generation and project setup) are always validated in CI and any breakage is caught early.

## Actors
- Developers
- Test automation (CI/CD)
- Onboarding maintainers

## Preconditions
- The API is running and accessible
- `onboarding_paths.json` defines a `test_path` with representative onboarding steps
- Automated tests (e.g., `tests/test_onboarding_flow.py`) are present and enabled

## Step-by-Step Actions
1. **Define a test onboarding path:**
   - Add a `test_path` entry to `onboarding_paths.json` with steps that exercise token generation, namespace creation, and onboarding validation.
   - Example steps:
     - `obtain_api_token`
     - `create_project_namespace`
     - `configure_namespace_permissions`
     - `create_namespace_token`
     - `submit_first_rule`
     - `run_onboarding_health_check`
2. **Write an automated test:**
   - Use the `test_path` in onboarding tests (e.g., `tests/test_onboarding_flow.py`).
   - The test should:
     - POST to `/onboarding/init` with a unique project name and `path: test_path`
     - Assert status 200 and correct onboarding steps are created
     - Mark each step as complete and verify progress
     - Fail if any step returns a non-200 status
3. **Run tests in CI:**
   - Ensure onboarding tests are part of the standard test suite and run on every commit/PR.
   - Any onboarding regression will fail CI and require immediate attention.

## Expected Outcomes
- Onboarding logic is always validated and never drifts from reality
- Token generation and onboarding flows are guaranteed to work
- Developers can safely refactor onboarding knowing tests will catch regressions
- New onboarding features can be added with confidence

## Best Practices
- Use a dedicated onboarding path for test automation (`test_path`)
- Keep test onboarding steps minimal but representative
- Use unique project names in tests to avoid DB pollution
- Document onboarding paths and test logic for maintainability
- Review onboarding user stories and update as onboarding evolves

## References
- `onboarding_paths.json`
- `tests/test_onboarding_flow.py`
- `/onboarding/init` and `/onboarding/progress/{project_name}` endpoints 
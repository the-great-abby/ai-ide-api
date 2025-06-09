# User Story: Onboarding Token Bootstrap After Test DB Reset

## Motivation
When the test database is wiped and re-initialized, all previously created tokens are lost. The onboarding process must generate new user and admin tokens for the new database state. This ensures that tests and admin flows do not fail due to missing or mismatched tokens.

## Actors
- Developer running tests or onboarding scripts
- Test automation system
- FastAPI backend (token endpoints)

## Preconditions
- The test database has been wiped/reset (e.g., via `ai-test-setup` or `ai-test-with-setup`)
- No tokens exist in the new database

## Actions
1. The onboarding script or test setup attempts to create a user token.
2. The script uses the new user token to bootstrap the first admin token.
3. All subsequent API calls use the newly generated tokens for authentication.

## Expected Outcomes
- The onboarding process succeeds, generating new user and admin tokens for the new DB state.
- No errors occur due to missing or mismatched tokens.
- Tests and admin flows proceed using the new tokens.

## Best Practices
- Always generate new tokens after a test DB reset.
- Do not rely on tokens from a previous DB state.
- Document this edge case in onboarding and test setup docs.
- If onboarding fails due to missing tokens, re-run the onboarding script to generate fresh tokens.

## References
- `ai-test-setup`, `ai-test-with-setup` Makefile targets
- Token creation endpoints in FastAPI backend 
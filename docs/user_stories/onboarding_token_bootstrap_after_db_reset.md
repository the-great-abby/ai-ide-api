# User Story: Onboarding Token Bootstrap After DB Reset

## Motivation
When the test or production database is reset, all API tokens—including the admin token—are deleted. To restore admin access and allow tests or onboarding to proceed, the onboarding flow must be re-triggered to generate new tokens. Failing to do so results in authentication errors and failed tests.

## Actors
- Developer
- Test automation
- Onboarding scripts

## Preconditions
- The database has been reset or wiped (e.g., via `make test-db-reset` or as part of `quickstart`).
- No valid tokens exist in the database.

## Step-by-Step Actions
1. **Create a user token** using the `/admin/generate-token` endpoint (role: user, no Authorization header required).
2. **Use the new user token** to call `/admin/generate-token` again, this time requesting an admin token (role: admin, Authorization: Bearer <user_token>).
3. **Use the new admin token** for all subsequent admin actions and tests.

## Expected Outcomes
- The system is re-initialized with a valid user and admin token.
- All endpoints requiring admin access work as expected.
- Tests and onboarding scripts do not fail due to invalid or missing tokens after a DB reset.

## Best Practices
- Always re-bootstrap tokens after a DB reset.
- Do not cache or reuse tokens across DB resets in test fixtures.
- Automate the onboarding flow in test setup scripts.
- Document this edge case for all developers and CI/CD pipelines. 
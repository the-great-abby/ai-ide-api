# Troubleshooting: Token Errors After Test DB Reset

## Common Error Messages

| Error Message                                      | Cause                        | Corrective Action                |
|----------------------------------------------------|------------------------------|----------------------------------|
| 401: "A valid admin API token is required..."      | No valid admin token         | Re-bootstrap onboarding flow     |
| 401: "Invalid or inactive token"                   | Token missing/expired/wiped  | Re-bootstrap onboarding flow     |
| 401/403: "Insufficient role"                       | Wrong token type             | Use correct token (admin/user)   |

## Why This Happens
- When the test database is reset, all tokens (including admin) are deleted.
- Any cached or previously created token becomes invalid.
- Tests or scripts that use old tokens will fail with 401/403 errors.

## Best Practices
- Always use the `admin_token` or `admin_headers` fixture in tests that require admin access.
- Never cache tokens across test sessions or after a DB reset.
- Automate the onboarding flow in test setup scripts.
- Document this edge case for all developers and CI/CD pipelines.

## Global Runtime Check
- The test fixture now includes a runtime check: if the admin token is invalid, it will re-bootstrap the onboarding flow and create a new admin token.
- This ensures that after a DB reset, all tests get a valid token automatically.

## What To Do If You See These Errors
- Ensure your test uses the correct fixture (`admin_token` or `admin_headers`).
- If you are writing a new test, always use the onboarding-compliant fixture for token creation.
- If you see repeated 401/403 errors, check if the DB was reset and if the test is using a stale token.

## References
- See also: `docs/user_stories/onboarding_token_bootstrap_after_db_reset.md` for the full user story and onboarding flow. 
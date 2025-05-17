---
title: API Token Onboarding and Error Log Lookup for AI IDEs
date: 2024-05-17
authors: [ai-ide-team]
---

# User Story: API Token Onboarding and Error Log Lookup for AI IDEs

## Motivation
To enable secure, individualized access for other AI IDEs and client systems, we provide a self-service onboarding flow for generating API tokens. These tokens allow clients to access protected endpoints, such as error log lookup, without manual admin intervention. This improves integration, support, and troubleshooting for external users.

## Actors
- AI IDE developers integrating with the API
- System administrators
- Automated onboarding scripts

## Preconditions
- The API server is running and accessible
- The database schema includes the `api_access_tokens` and `api_error_logs` tables

## Workflow
1. **Token Generation**
    - The user (or onboarding script) calls `POST /admin/generate-token` with an optional description and creator name.
    - The API returns a new, unique token (shown only once).
    - The user stores this token securely for future use.
2. **Token Usage**
    - The user includes the token in the `Authorization: Bearer ...` header for protected endpoints (e.g., `/admin/errors/{error_id}`).
    - The API validates the token against the database, ensuring it is active.
3. **Error Log Lookup**
    - When an error occurs, the API returns a reference error ID in the response.
    - The user can query `/admin/errors/{error_id}` with their token to retrieve error details for debugging.
4. **Token Management** (future)
    - Users or admins can list, revoke, or rotate tokens as needed.

## Expected Outcomes
- Secure, auditable access to sensitive endpoints
- Improved onboarding and support for external AI IDEs
- Easier troubleshooting and error reporting via error IDs

## Best Practices
- Store tokens securely; treat them like passwords
- Revoke tokens if compromised or no longer needed
- Rotate tokens periodically for security
- Never expose tokens in public code or logs

## References
- See also: `api_access_tokens` and `api_error_logs` models in `db.py`
- Error logging middleware and endpoints in `rule_api_server.py` 
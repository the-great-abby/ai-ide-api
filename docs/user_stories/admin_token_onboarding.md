# Admin Token Onboarding User Story

## Motivation
To ensure secure and auditable onboarding, the system requires a valid (non-admin) API token to generate the first admin token. This prevents unauthenticated or anonymous creation of privileged tokens and provides a clear, repeatable onboarding flow.

## Actors
- New user (developer, admin, or operator)
- API server

## Preconditions
- No admin tokens exist in the system (fresh install or after a full reset)
- User has access to the API server

## Step-by-Step Actions

```mermaid
flowchart TD
    A[Start: No admin tokens exist] --> B[User requests normal API token (role: user)]
    B --> C[API server issues normal token]
    C --> D[User requests admin token using normal token in Authorization header]
    D --> E[API server verifies normal token is valid]
    E --> F[API server creates first admin token]
    F --> G[User receives admin token]
    G --> H[Subsequent admin token requests require admin token in Authorization header]
```

## Expected Outcomes
- The first admin token can only be created by a user who already has a valid (non-admin) API token.
- All subsequent admin token creations require an existing admin token.
- Unauthenticated or blank requests to create an admin token are rejected.

## Best Practices
- Store your normal and admin tokens securely; treat them like passwords.
- Rotate tokens regularly and revoke unused tokens.
- Never share admin tokens publicly or in code.
- Document the onboarding process for your team.

## 🛡️ API Access & Token Flow (Updated June 2024)

- **API Port for Host Access:** Always use `http://localhost:9104` to access the API from your host machine. Never use `localhost:8000` or `localhost:9103` for direct API access from the host.
- **Internal Docker Service:** Use `test-api:8000` for service-to-service communication within the Docker test network.
- **Token Requirement:** All endpoints except `/onboarding-init` require a valid token. Always start onboarding by calling `/onboarding-init` to obtain a token.

### Example: Obtain Normal and Admin Token (Host Machine)

```bash
# Step 1: Obtain normal token
curl -X POST http://localhost:9104/onboarding-init \
  -H "Content-Type: application/json" \
  -d '{"project_name": "bootstrap-project"}'
# Use the returned token for the next step

# Step 2: Create a normal API token (if needed)
curl -X POST http://localhost:9104/admin/generate-token \
  -H "Authorization: Bearer <bootstrap-token>" \
  -H "Content-Type: application/json" \
  -d '{"description": "Bootstrap user token", "role": "user"}'

# Step 3: Create the first admin token
curl -X POST http://localhost:9104/admin/generate-token \
  -H "Authorization: Bearer <normal-user-token>" \
  -H "Content-Type: application/json" \
  -d '{"description": "Admin token", "role": "admin"}'
```

## References
- See also: `api_access_tokens` model in `db.py`
- Error logging and onboarding docs in `/onboarding/docs` 
# User Story: Project Name Lookup and UUID Mapping

## Motivation
As a developer or API client, I want to use human-readable project names when interacting with the API, while the system ensures all internal operations use UUIDs for consistency and referential integrity. This allows for easy onboarding, scripting, and integration without requiring clients to manage UUIDs.

## Actors
- API clients (users, scripts, onboarding tools)
- Backend developers
- System administrators

## Preconditions
- The `projects` table exists in the database, with both a `name` (string) and an `id` (UUID primary key).
- The API has access to a function like `get_or_create_project_by_name` to resolve names to UUIDs.

## Step-by-Step Actions
1. **Client sends a project name** (e.g., `"test-project"`) in API requests.
2. **API receives the request** and extracts the project name.
3. **API calls `get_or_create_project_by_name(db, name, ...)`**:
    - If the project exists, retrieves the UUID.
    - If not, creates a new project with the given name and generates a UUID.
4. **API uses the UUID** for all downstream database operations (rules, proposals, feedback, etc.).
5. **API can return both the project name and UUID** in responses for client reference.

## Expected Outcomes
- Clients can use simple, human-readable project names.
- The system maintains a consistent mapping of names to UUIDs.
- All internal references use UUIDs, ensuring referential integrity.
- No more UUID errors in tests or API calls when using project names.

## Best Practices
- Always use the lookup function to resolve project names to UUIDs in the API layer.
- Never require clients to generate or manage UUIDs for projects.
- Return both the name and UUID in API responses when relevant.
- Document this workflow in onboarding and API docs.

## References
- `db.py` Project model and `get_or_create_project_by_name` function
- Example endpoints: `/proposals`, `/rules`, `/onboarding/init`

## Global Scope UUID

- The system uses a reserved UUID for global-scope rules: `99999999-9999-9999-9999-999999999999`
- This value is defined in `.env` as `GLOBAL_SCOPE_UUID` and must match the value in the codebase.
- All global-scope rules and proposals use this UUID for `scope_id`.
- Reference this value in onboarding, documentation, and when debugging global rule logic. 
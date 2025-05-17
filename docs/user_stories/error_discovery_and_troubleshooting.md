# User Story: Error Discovery and Troubleshooting Workflow

## Motivation
To streamline debugging and resolution, the system provides Reference IDs for errors. This enables developers and AI assistants to quickly discover, investigate, and resolve issues by looking up error details, reviewing logs, and examining relevant code.

## Actors
- Developers
- AI assistants
- System administrators

## Preconditions
- The API server is running and accessible
- Error logging and Reference ID generation are enabled
- The error lookup endpoint (`/admin/errors/{error_id}`) is available

## Step-by-Step Actions
1. An error occurs anywhere in the system (e.g., API returns a 500 or 422 error with a Reference ID).
2. The user or developer notes the Reference ID from the error response.
3. The user looks up the error details using the Reference ID:
    ```bash
    curl -H "Authorization: Bearer <admin-token>" http://localhost:9103/admin/errors/<error_id>
    ```
4. Review the error details and stack trace returned by the API.
5. Check related logs for additional context (e.g., via Docker logs or log aggregation tools).
6. Examine the relevant code (using the stack trace and endpoint info) to diagnose the root cause.
7. Apply a fix or mitigation as needed.
8. Optionally, update documentation or user stories if the error reveals a gap in process or onboarding.

## Expected Outcomes
- Errors are quickly discoverable and traceable using Reference IDs.
- Developers and AI assistants can efficiently diagnose and resolve issues.
- System reliability and user trust are improved.

## Best Practices
- Always include the Reference ID when reporting or discussing errors.
- Use the error lookup endpoint as the first step in troubleshooting.
- Keep logs accessible and well-structured for rapid investigation.
- Document recurring or complex errors in user stories or onboarding guides.

## Example
> **Error Response:**
> ```json
> {"detail": "Internal server error. Reference ID: 123e4567-e89b-12d3-a456-426614174000"}
> ```
>
> **Troubleshooting Steps:**
> 1. Look up the error: `/admin/errors/123e4567-e89b-12d3-a456-426614174000`
> 2. Review stack trace and logs
> 3. Diagnose and fix the code

---

**See also:**
- [bug_report_with_user_story.md](bug_report_with_user_story.md)
- [api_token_onboarding.md](api_token_onboarding.md) 
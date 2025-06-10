# API Status Code Guide

This guide summarizes the meaning and usage of HTTP status codes in the API, with examples for validation, business logic, and authentication scenarios. Use this as a reference for debugging, test writing, and endpoint design.

| Status Code | Meaning                                 | When to Use / Example Scenario                                 |
|-------------|-----------------------------------------|---------------------------------------------------------------|
| 200 OK      | Success                                 | Standard response for successful GET, POST, PATCH, etc.        |
| 201 Created | Resource created                        | After successful POST that creates a new resource              |
| 204 No Content | Success, no response body            | After successful DELETE or update with no content to return    |
| 400 Bad Request | Malformed input or request           | Invalid JSON, bad query/path param, wrong data type            |
| 401 Unauthorized | Not authenticated                   | Missing or invalid auth token                                 |
| 403 Forbidden | Authenticated, but not allowed        | Valid token, but insufficient permissions                     |
| 404 Not Found | Resource does not exist               | ID/path does not match any resource                           |
| 409 Conflict | Business logic conflict                | Duplicate resource, version conflict, etc.                    |
| 422 Unprocessable Entity | Validation error             | Missing required field, invalid enum, failed Pydantic check   |
| 500 Internal Server Error | Unexpected server error      | Unhandled exception, bug, or DB failure                       |

## Examples
- **200 OK:** GET /rules/1234 (rule exists)
- **201 Created:** POST /propose-rule-change (new proposal created)
- **204 No Content:** DELETE /rules/1234 (rule deleted)
- **400 Bad Request:** POST /propose-rule-change with malformed JSON
- **401 Unauthorized:** GET /rules (no token provided)
- **403 Forbidden:** POST /rules (user token lacks admin role)
- **404 Not Found:** GET /rules/does-not-exist
- **409 Conflict:** POST /propose-rule-change (identical pending proposal exists)
- **422 Unprocessable Entity:** POST /propose-rule-change with missing required field or invalid UUID
- **500 Internal Server Error:** Any endpoint if an unhandled exception occurs

## Best Practices
- Use 422 for semantic validation errors (body/fields), 400 for malformed input, 404 for not found, 401/403 for auth, and 409 for true business conflicts.
- Always include a clear, actionable error message in the response body for 4xx/5xx errors.
- Align test assertions and endpoint logic with this guide for consistency.

## Further Reading
- [User Story: Validation Consistency Across the API](validation_consistency.md) 
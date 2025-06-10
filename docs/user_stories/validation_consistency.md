# User Story: Validation Consistency Across the API

## Motivation
To ensure robust, predictable, and user-friendly behavior, all API endpoints must enforce strict validation of input data. Consistent validation prevents ambiguous errors, improves client experience, and enables reliable automated testing. This is especially important for fields like UUIDs, enumerated types, and required fields, where silent failures or inconsistent status codes can lead to confusion and bugs.

## Actors
- API Consumer (developer, automation, or integration)
- API Maintainer (backend engineer, QA)
- Automated Test Suite

## Preconditions
- The API exposes endpoints that accept user input (e.g., IDs, payloads, query parameters).
- The system uses UUIDs for resource identification and expects certain fields to be present and correctly typed.

## Step-by-Step Actions
1. **Client Submits a Request:**
   - The client sends a request to an API endpoint, providing all required fields (e.g., UUIDs, enums, strings, lists).
2. **Input Validation:**
   - The API validates all incoming data:
     - Checks that UUIDs are valid and well-formed.
     - Ensures required fields are present and of the correct type.
     - Validates enums and allowed values (e.g., feedback types).
     - Rejects extra or unknown fields if not allowed.
3. **Error Handling:**
   - If validation fails:
     - The API returns a `422 Unprocessable Entity` (for body/field validation errors) or `400 Bad Request` (for malformed input, such as an invalid UUID in the path).
     - The error response includes a clear message indicating the cause (e.g., "Invalid UUID format", "Missing required field: description").
4. **Success Path:**
   - If validation passes, the API processes the request and returns the appropriate success status code (e.g., `200 OK`, `201 Created`).
5. **Test Coverage:**
   - Automated tests cover both valid and invalid input scenarios, asserting that the correct status codes and error messages are returned for each case.

## Expected Outcomes
- Clients receive immediate, clear feedback when input is invalid.
- Status codes are consistent across all endpoints for similar validation failures.
- Automated tests can reliably assert on both success and failure cases.
- The API is easier to maintain and extend, with fewer hidden bugs.

## Best Practices
- Use Pydantic models and FastAPI validation features for request bodies and query parameters.
- Validate UUIDs in path and query parameters, returning `400` or `422` as appropriate.
- Document all required fields and allowed values in the API schema and user stories.
- Ensure error messages are actionable and specific.
- Align test assertions with the documented validation behavior and status codes.

## Further Reading
- [User Story: Submitting a Rule Proposal](rule_proposal_submission.md)
- [User Story: Providing Feedback on Rule Proposals](rule_proposal_feedback_types.md)

## Validation Matrix: Inputs, Error Codes, and Example Messages

| Scenario                                 | Input Type      | Expected Error Code | Example Error Message                       |
|------------------------------------------|-----------------|--------------------|---------------------------------------------|
| Missing required field                   | Body/JSON       | 422                | 'Missing required field: description'       |
| Invalid UUID in path                     | Path/Query      | 400 or 422         | 'Invalid UUID format'                       |
| Invalid enum value (e.g., feedback type) | Body/JSON       | 422                | 'Value is not a valid enumeration member'   |
| Extra/unknown field in body              | Body/JSON       | 422                | 'Extra fields not permitted'                |
| Wrong type (e.g., string for int)        | Body/Query      | 422                | 'value is not a valid integer'              |
| Malformed JSON                           | Body            | 400                | 'Malformed request body'                    |
| Resource not found                       | Path/Query      | 404                | 'Resource not found'                        |
| Conflict (e.g., duplicate rule)          | Body/Business   | 422                | 'Rule already exists/conflict detected'     |
| Unauthorized/missing token               | Header/Auth     | 401                | 'Not authenticated'                         |
| Forbidden/insufficient permissions       | Header/Auth     | 403                | 'Not enough permissions'                    |

> **Note:** Use 422 for semantic validation errors (body/fields), 400 for malformed input (e.g., bad UUID, bad JSON), 404 for not found, 401/403 for auth, and 409 for true business conflicts if needed. 
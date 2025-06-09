# Error Handling & Logging Guide

This guide explains how errors are caught, logged, and surfaced in this project—covering both backend (FastAPI) and frontend (React), with best practices and troubleshooting tips.

---

## 1. Overview
- **Goal:** Ensure errors are caught, logged, and surfaced in a way that's helpful for both users and developers.
- **Scope:** Backend (FastAPI), frontend (React), and supporting infrastructure (logging config, error response patterns).

---

## 2. Key Concepts
- **Error Types:**
  - *User errors* (bad input, unauthorized, not found)
  - *System errors* (database down, unhandled exceptions)
  - *Validation errors* (schema, type, or business rule violations)
- **Logging:**
  - All errors should be logged with enough context to debug the issue.
  - Use structured logging (not print statements) for consistency and searchability.
- **Error Responses:**
  - API returns clear, consistent error responses (status code, message, optional details).
  - Frontend displays user-friendly messages and logs technical details for debugging.

---

## 3. Backend Error Handling (FastAPI)
- **Exception Handlers:** Custom handlers for common error types (e.g., 422 validation, 404 not found, 500 internal error).
- **Logging:** Use the project's logger (not print) to record errors, including stack traces for unexpected exceptions.
- **Error Response Format:**
  ```json
  {
    "detail": "Invalid input",
    "code": 422,
    "errors": [
      {"field": "email", "message": "Invalid email address"}
    ]
  }
  ```
- **Example:**
  ```python
  from fastapi import Request, HTTPException
  from fastapi.responses import JSONResponse
  import logging

  logger = logging.getLogger(__name__)

  @app.exception_handler(HTTPException)
  async def http_exception_handler(request: Request, exc: HTTPException):
      logger.error(f"HTTP error: {exc.detail}", exc_info=True)
      return JSONResponse(
          status_code=exc.status_code,
          content={"detail": exc.detail, "code": exc.status_code}
      )
  ```

---

## 4. Frontend Error Handling (React Admin UI)
- **API Error Handling:**
  - Catch errors from API calls and display user-friendly messages.
  - Optionally log errors to a monitoring service (e.g., Sentry).
- **Example:**
  ```js
  try {
    const response = await api.post('/propose-rule', data);
    // handle success
  } catch (error) {
    setError(error.response?.data?.detail || 'Something went wrong');
    // Optionally: log error details for debugging
  }
  ```

---

## 5. Logging Configuration
- **Centralized Logging:** Use Python's `logging` module with a project-wide config (see `logging_config.py`).
- **Log Levels:** Use appropriate levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- **No Print Statements:** Always use logger for output, especially in migrations and scripts.

---

## 6. Common Error Patterns & Files
- **Error Response Files:** `error_response.json`, `error_response_422.json`, etc. in the repo for reference and testing.
- **Reusable Error Utilities:** Functions or classes for generating standard error responses.

---

## 7. Best Practices
- Always log errors with enough context (request info, user ID, etc.).
- Never expose sensitive info in error messages.
- Use structured, consistent error responses.
- Test error cases (unit/integration tests for error handling).
- Document common error codes and meanings.

---

## 8. Common Pitfalls & Troubleshooting
| Symptom                        | Likely Cause                                  | Solution                                      |
|--------------------------------|-----------------------------------------------|-----------------------------------------------|
| "No error logged"              | Used print instead of logger                  | Use logger everywhere                         |
| "Unhelpful error message"      | Error not caught or not descriptive           | Add custom exception handlers, improve messages|
| "Frontend shows raw error"     | API returns technical details                 | Return user-friendly messages, log details    |
| "Silent failure"               | Error swallowed, not logged or surfaced       | Ensure all exceptions are caught and logged   |

---

## 9. Advanced: Monitoring & Alerting
- Integrate with tools like Sentry, Datadog, or ELK for error monitoring and alerting.
- Set up alerts for critical errors or repeated failures.

---

## 10. Further Reading
- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)

---

*See something missing? Please add your tips or examples!* 
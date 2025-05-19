# User Story: SQLAlchemy Limitations with AI Memory Vector Store

> **Note (2025-05-18):** Embedding is now always generated server-side. Test code and API clients should NOT provide embedding; the backend handles it automatically.

## Motivation
As a developer, I want to understand the limitations and tradeoffs of using SQLAlchemy with custom Postgres types (like pgvector) for AI memory and vector search, so I can make informed decisions about when to use the ORM and when to switch to raw SQL or a lower-level driver.

## Actors
- Developer
- AI system maintainer
- Knowledge engineer

## Symptoms / Issues
- SQLAlchemy does not natively convert custom Postgres types (like `vector`) to Python types (like `list`).
- When fetching rows, vector fields may be returned as strings (e.g., `"[0.1,0.2,...]"`) instead of Python lists.
- FastAPI response validation errors occur if the API expects a list but receives a string.
- Extra conversion code is needed to ensure API responses are in the correct format.

## Workarounds
- Add conversion logic in API endpoints to convert vector fields from strings to lists before returning responses.
- Use `ast.literal_eval` or similar to safely parse string representations of vectors.
- Patch all endpoints that return vector fields to ensure correct serialization.

## When to Consider Switching
- If conversion code becomes widespread and hard to maintain.
- If you need maximum performance for vector search and retrieval.
- If you want direct control over custom types and SQL queries.
- If you want to use async database drivers (e.g., `asyncpg`).

## Alternative Approaches
- Use `psycopg2` or `asyncpg` directly for vector operations, and SQLAlchemy for other tables.
- Use only raw SQL for all vector store operations.
- Consider a hybrid approach: ORM for most tables, raw SQL for performance-critical or custom-type tables.

## Best Practices
- Document all conversion logic and its necessity.
- Regularly review the codebase for places where custom type conversion is needed.
- Monitor the cost/benefit of continuing with SQLAlchemy as requirements evolve.
- Add tests to ensure API responses always return the correct types.

## Example Symptom
- FastAPI endpoint returns a 500 error with:
  `fastapi.exceptions.ResponseValidationError: ... 'embedding' ... 'Input should be a valid list' ...`
- Root cause: SQLAlchemy returns a string for the vector field, but the API expects a list.

## References
- [rule_api_server.py](../rule_api_server.py)
- [db.py](../db.py)
- [pgvector docs](https://github.com/pgvector/pgvector)
- [SQLAlchemy custom types](https://docs.sqlalchemy.org/en/20/core/custom_types.html) 
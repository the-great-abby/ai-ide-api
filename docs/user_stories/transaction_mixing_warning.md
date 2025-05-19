# User Story: Warning—Mixing SQLAlchemy ORM and Raw psycopg2/asyncpg in the Same Transaction

## Motivation
As a developer, I want to be warned before mixing SQLAlchemy ORM operations and raw psycopg2/asyncpg queries in the same transaction or request, so I can avoid subtle bugs, data consistency issues, and hard-to-debug errors.

## Scenario
- I am building a FastAPI endpoint (or any Python service) that uses both SQLAlchemy ORM and raw SQL (psycopg2 or asyncpg) in the same logical transaction or request.
- I want all operations to be atomic (all succeed or all fail together).

## Warning
**STOP!**
Mixing SQLAlchemy ORM and raw psycopg2/asyncpg operations in the same transaction/session can lead to:
- Uncommitted changes in the ORM session not being visible to raw SQL queries (and vice versa).
- Transaction state getting out of sync between the ORM and raw connections.
- Data consistency issues, lost updates, or phantom reads.
- Extremely hard-to-debug bugs, especially under load or in production.

## Symptoms
- You write to the database with SQLAlchemy, then try to read with psycopg2 in the same request—but the new data isn't there.
- You commit with psycopg2, but SQLAlchemy's session doesn't see the change until you refresh or restart the session.
- Transaction rollbacks don't affect all operations as expected.

## Best Practices
- **Do NOT mix SQLAlchemy ORM and raw SQL in the same transaction/session.**
- If you need to use both, keep them in separate endpoints or requests, each with their own connection/transaction.
- If you must mix, use the same underlying connection (advanced, not recommended for most cases).
- Document any exceptions to this rule and add tests to catch issues.

## Example (What NOT to do)
```python
# BAD: Mixing ORM and raw SQL in the same request
session = SessionLocal()
session.add(MyModel(...))
# ...
conn = psycopg2.connect(...)
cur = conn.cursor()
cur.execute("SELECT * FROM my_table WHERE ...")  # May not see uncommitted ORM changes
```

## Example (Safe)
```python
# GOOD: Use only one method per endpoint/request
# Option 1: All ORM
session = SessionLocal()
# ... all operations ...
session.commit()

# Option 2: All raw SQL
conn = psycopg2.connect(...)
# ... all operations ...
conn.commit()
```

## References
- [SQLAlchemy FAQ: How can I use raw SQL with the ORM?](https://docs.sqlalchemy.org/en/20/faq/sessions.html#faq-mixing-orm-and-core)
- [FastAPI docs: SQL (Relational) Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/) 
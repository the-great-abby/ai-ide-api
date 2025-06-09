## Postgres CLI Output Best Practice

When running psql commands in scripts, Makefiles, or during troubleshooting, **always pipe the output to `cat`**. This disables the pager and ensures output is non-interactive and CI/CD safe.

**Example:**
```bash
docker compose exec test-db psql -U postgres -d rulesdb -c '\dt' | cat
docker compose exec test-db psql -U postgres -d rulesdb -c '\d my_table' | cat
```

## Docker Postgres Service Names

| Environment | Service Name |
|-------------|--------------|
| Dev/Prod    | db           |
| Test/CI     | test-db      |

> **Note:** All general usage, onboarding, and code samples use `db` as the default Postgres service/container. Use `test-db` only for test/CI environments or when running tests.
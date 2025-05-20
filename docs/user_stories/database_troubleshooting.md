## Postgres CLI Output Best Practice

When running psql commands in scripts, Makefiles, or during troubleshooting, **always pipe the output to `cat`**. This disables the pager and ensures output is non-interactive and CI/CD safe.

**Example:**
```bash
docker compose exec db-test psql -U postgres -d rulesdb -c '\dt' | cat
docker compose exec db-test psql -U postgres -d rulesdb -c '\d my_table' | cat
```

This practice prevents issues where output is paged (e.g., with `less` or `more`), which can cause scripts to hang or output to be lost in automated environments. 
## ARR! UUIDs vs Strings for IDs and Foreign Keys

All ID columns and foreign keys in this codebase are `sa.String()` (VARCHAR), not native UUID. This be for maximum compatibility with SQLAlchemy, Alembic, and Postgres across all versions. If ye pass a `uuid.UUID` object to a query, cast it to `str()` first, or ye'll be walkin' the plank!

**Why?**
- Native UUID columns and FKs cause endless trouble with migrations, drivers, and test data.
- Mixing types (UUID in one table, String in another) is the path to madness and broken FKs.
- String columns work everywhere, but ye lose strict type safety.

**If ye ever want to switch to native UUIDs:**
- Ye must update *all* models, migrations, and test data at once, or face the wrath of broken foreign keys and migration errors.

See [`rules/db_types.mdc`](../../rules/db_types.mdc) for the full tale and best practices.

---

## Obtaining an Admin Token After Onboarding

After you complete `/onboarding/init`, you will receive a user API token (saved in `.apitoken` and `.api_info_capture`).

**To obtain an admin token:**
1. Use the user token as the `Authorization` header in a call to `/admin/generate-token`.
2. Specify `"role": "admin"` and your `project_id` in the request body.

**Example:**

```bash
curl -X POST http://localhost:9103/admin/generate-token \
  -H "Authorization: Bearer <user-token-from-init>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Admin token for LLM access",
    "role": "admin",
    "project_id": "<project_id-from-init>"
  }'
```

- The response will contain your new admin token.
- Use this admin token for all admin-level API actions, such as enabling LLM access for your project.

> **Note:** This is a required bootstrap step for admin access. You cannot generate an admin token without first completing onboarding and using the user token. 
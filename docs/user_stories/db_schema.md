# User Story: Schema Verification via Makefile

**As a developer or maintainer,**
I want to quickly verify the schema of any database table using a Makefile target,
so that I can ensure migrations have been applied correctly, debug issues, and confirm the presence of required columns (such as `user_story`).

---

## Acceptance Criteria
- I can run a single Makefile target to view the schema of any table in the database.
- The target outputs the column names, types, and indexes for the specified table.
- The workflow is documented in onboarding and troubleshooting guides.
- The target is referenced in developer documentation for schema and migration troubleshooting.

---

## Example Workflow

1. **Check the schema for the `rules` table:**
   ```bash
   make -f Makefile.ai schema-table TABLE=rules
   ```
2. **Check the schema for the `proposals` table:**
   ```bash
   make -f Makefile.ai schema-table TABLE=proposals
   ```
3. **Review the output to confirm the presence of required columns (e.g., `user_story`).**
4. **If a column is missing, run migrations or investigate further.**

---

## Best Practices
- Use the schema check target after restoring a backup or running migrations.
- Reference this workflow in onboarding and troubleshooting documentation.
- Encourage all contributors to verify schema before reporting data or API issues. 
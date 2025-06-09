# Alembic Head Merge Process

## When to Merge
- Multiple heads detected by `alembic heads`
- Parallel development or merge conflicts in migration history

## Steps
1. **List heads:**
   - `make -f Makefile.ai-test test-db-heads`
   - or `docker-compose -f docker-compose.test.yml exec test-api alembic heads`
2. **Inspect migration history:**
   - `docker-compose -f docker-compose.test.yml exec test-api alembic history --verbose`
   - Trace each head back to the last common ancestor.
3. **Review each head migration file for schema changes:**
   - Open each migration file for the heads in your editor.
   - Check for conflicting or overlapping changes.
4. **Check for conflicts or overlaps:**
   - Compare changes in each branch.
   - Resolve any conflicts before merging.
5. **Plan and create a merge migration:**
   - Use: `docker-compose -f docker-compose.test.yml exec test-api alembic merge <head1> <head2> -m "merge heads"`
   - Add more heads as needed.
6. **Review and test the merge:**
   - Open the merge migration and verify its `down_revision` and `revision`.
   - Ensure it contains no unintended schema changes.
   - Run: `make -f Makefile.ai-test test-db-migrate` to apply all migrations and confirm the database is in the expected state.
7. **Document the merge:**
   - In the merge migration file, add a comment explaining why the merge was needed and what branches were merged.
   - Optionally, add a user story or note in your documentation for future reference.

## Best Practices
- Never merge heads without reviewing the changes in each branch.
- Always resolve conflicts before merging.
- Test the merged schema in a fresh database.
- Document the reason for the merge and any manual steps taken. 
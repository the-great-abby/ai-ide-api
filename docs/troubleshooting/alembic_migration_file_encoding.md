# Alembic Migration File Encoding/Formatting Issues

## Problem
Alembic fails to recognize migration files, reporting errors like:

```
Could not determine revision id from filename ... Be sure the 'revision' variable is declared inside the script
```

Even though the `revision` and `down_revision` variables are present and appear correct in the file.

## Symptoms
- Alembic cannot upgrade/downgrade and reports it cannot determine the revision id.
- Migration files look correct in a text editor, but Alembic ignores them.
- Re-saving or touching the file sometimes fixes the issue.

## Root Cause
- The migration file contains hidden characters, non-ASCII formatting, or a byte order mark (BOM) due to copying, editing in certain editors, or moving between systems.
- Alembic's parser is strict and will not recognize the `revision` variable if there are encoding or formatting issues.

## Diagnosis
- The error persists even after checking that `revision` and `down_revision` are present and correct.
- The file was recently copied, moved, or edited in a non-plain-text editor.
- Recreating the file from scratch in a plain text editor resolves the issue.

## Solution
1. **Recreate the migration file from scratch:**
   - Use a plain text editor (e.g., VS Code, Sublime Text, vim, nano).
   - Copy only the ASCII content, and retype the `revision` and `down_revision` lines.
   - Save the file as UTF-8 **without BOM**.
2. **Check for hidden characters:**
   - Use `cat -A <filename>` or `xxd <filename>` to look for non-printable characters.
3. **Re-save and re-run Alembic:**
   - After recreating, Alembic should recognize the file and apply the migration.

## Best Practices
- Always use plain text editors for Alembic migration files.
- Avoid copying migration files between systems with different line endings or encodings.
- If you see this error, suspect encoding/formatting first—even if the file looks correct.

---

**Reference:**
This issue was encountered and resolved in the `ai-ide-api` project (June 2025). 
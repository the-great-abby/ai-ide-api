# Onboarding Another AI-IDE

Welcome! This document is your comprehensive onboarding guide for integrating another AI IDE or agent into the AI-IDE API project. Please follow these steps to ensure seamless collaboration, automation, and rule management.

---

# 🚀 Improved Initial Prompt for Onboarding AI IDEs/Agents

> **You are being onboarded as an AI IDE agent for a project using the AI-IDE Rule Management System. Follow these steps exactly:**
>
> 1. **Sync all approved rules from the central rule server:**
>    - Connect to the API at `http://localhost:9103` (or the provided server URL).
>    - Use the `/rules` endpoint to fetch all approved rules.
>    - Save the results as a `.mdc` (Markdown Cursor) file in your `.cursor/rules/` directory (e.g., `rules.mdc`).
>    - The `.mdc` file must start with YAML frontmatter:
>      ```yaml
>      ---
>      description: "Fetched rules from the central rule server"
>      globs:
>        - .cursor/rules/rules.mdc
>      ---
>      ```
>    - **Never run tests or scripts directly—always use `Makefile.ai` targets for all automation.**
>
> 2. **When creating or proposing new rules:**
>    - **Draft the rule as a `.txt` file** in your workspace root.
>    - **Review and validate** the content for structure and clarity.
>    - **Rename/move** the file to `.cursor/rules/` with a `.mdc` extension.
>    - **Required YAML frontmatter:**
>      ```yaml
>      ---
>      description: "Clear, actionable summary of the rule."
>      globs:
>        - "glob/pattern/for/applicability"
>      ---
>      ```
>    - **Update the rule index** (`.cursor/rules/cursor_rules.mdc`) after adding a new rule.
>    - **After any rule changes, run:**
>      ```
>      make -f Makefile.ai admin-maintain-rules
>      ```
>
> 3. **For all automation (tests, builds, migrations):**
>    - Use only `Makefile.ai` targets.
>    - Use Docker service names and internal ports for all connections.
>
> 4. **If you need more details, refer to:**
>    - [ONBOARDING_OTHER_AI_IDE.md](https://github.com/the-great-abby/ai-ide-api/blob/main/ONBOARDING_OTHER_AI_IDE.md)
>    - [cursor_rules.mdc](mdc:.cursor/rules/cursor_rules.mdc)
>
> **If anything is unclear, ask clarifying questions before proceeding.**

---

## 🟢 Initial Prompts for Onboarding an AI IDE

Use the following copy-paste prompts to onboard an AI IDE agent. Choose the one that matches your situation:

### 1. Project Already In Progress

```
You are being onboarded as an AI IDE agent to an existing Rule Management System project.

**Your primary task:**
- Connect to the central AI-IDE API server at `http://localhost:9103` (or the provided server URL).
- Automatically fetch and sync all approved rules using the `/rules` endpoint.
- Save the results to a local `.mdc` (Markdown Cursor) file (e.g., `rules.mdc`).
- Use only the required YAML frontmatter fields in the `.mdc` file: `description` and `globs`.
- Place the `.mdc` file in your `.cursor/rules/` directory.
- Never run tests or scripts directly—always use `Makefile.ai` targets for all automation.
- Use Docker service names and internal ports for all connections (e.g., `db-test:5432`, `redis-test:6379`).

**API Discovery:**
- To discover all available endpoints and their request/response formats, fetch the OpenAPI schema from the API docs:
  - Visit the interactive docs at `http://localhost:9103/docs` in your browser.
  - For programmatic access, fetch the raw OpenAPI schema from `http://localhost:9103/openapi.json`.
- Parse this schema to list all endpoints, their methods, parameters, and expected responses.
- Use this information to generate client code, documentation, or integration tests as needed.

**Example .mdc rule file:**
```yaml
---
description: Fetch all approved rules from the central rule server for syncing.
globs:
  - .cursor/rules/fetch_remote_rules.mdc
---
```

If you need more details on automation, rule file structure, or best practices, refer to the [ONBOARDING_OTHER_AI_IDE.md](./ONBOARDING_OTHER_AI_IDE.md) document. If anything is unclear, ask clarifying questions before proceeding.
```

---

### 2. Starting a New Project from Scratch

```
You are setting up a new AI-IDE project. Please do the following:

1. **Create Makefile Targets for All Commands**
   - Add a `Makefile` and a `Makefile.ai` for AI-optimized workflows.
   - All test, build, and script commands should be run via `make` targets (e.g., `make -f Makefile.ai ai-test`).
2. **Set Up Docker for Isolation**
   - Add a `Dockerfile` and `docker-compose.yml` to run all services and builds in containers.
   - Do not run backend/frontend directly on the host—use Docker Compose for consistency.
3. **Configure Rule Syncing in .mdc Format**
   - Create a `.cursor/rules/` directory if it does not exist.
   - Create a `.txt` file with the following content, then rename it to `.mdc` after validation:
```yaml
---
description: Fetch all approved rules from the central rule server for syncing.
globs:
  - .cursor/rules/fetch_remote_rules.mdc
---
```
   - Place this file in `.cursor/rules/`.
4. **Connect to the API server at `http://localhost:9103` (or the provided server URL)** and use the `/rules` endpoint to fetch all approved rules.
5. **API Discovery:**
   - To discover all available endpoints and their request/response formats, fetch the OpenAPI schema from the API docs:
     - Visit the interactive docs at `http://localhost:9103/docs` in your browser.
     - For programmatic access, fetch the raw OpenAPI schema from `http://localhost:9103/openapi.json`.
   - Parse this schema to list all endpoints, their methods, parameters, and expected responses.
   - Use this information to generate client code, documentation, or integration tests as needed.
6. **Environment Setup**
   - Add example `.env` files and document required environment variables.
   - Never hardcode secrets or credentials.
7. **Testing and Linting**
   - Add make targets for testing (`ai-test`) and linting (`ai-lint`).
   - Use `make -f Makefile.ai ai-test PYTEST_ARGS="-x"` for tests.
8. **Documentation**
   - Add `ONBOARDING.md` and `INTEGRATING_AI_IDE.md` for setup and integration instructions.

If you need more details on automation, rule file structure, or best practices, refer to the [ONBOARDING_OTHER_AI_IDE.md](./ONBOARDING_OTHER_AI_IDE.md) document. If anything is unclear, ask clarifying questions before proceeding.
```

---

> **Key Principles:**
> - **All automation (tests, builds, migrations) MUST run through `Makefile.ai` targets.**
> - **Rule proposals are managed as `.mdc` files with YAML frontmatter.**
> - **Only `description` and `globs` are required in rule frontmatter.**
> - **All test and service connections use Docker service names and internal ports.**
> - **No direct use of `pytest`, `docker-compose`, or external ports.**

---

## 📦 Project Automation & Makefile.ai Usage

- **Run all tests, builds, and migrations via Makefile.ai:**
  ```sh
  make -f Makefile.ai ai-test PYTEST_ARGS="-x"
  make -f Makefile.ai ai-test-unit PYTEST_ARGS="-x"
  make -f Makefile.ai ai-test-integration PYTEST_ARGS="-x"
  make -f Makefile.ai ai-build
  make -f Makefile.ai ai-rebuild-all
  ```
- **Never run `pytest` or `docker-compose` directly.**
- **Always use the `-x` flag for tests** (stop on first failure).
- **Use Docker service names for all connections:**
  - `POSTGRES_HOST=db-test`, `POSTGRES_PORT=5432`
  - `REDIS_HOST=redis-test`, `REDIS_PORT=6379`
- **Default API port:** `9103` (update all configs accordingly).

---

## 📝 Rule File Creation & Management

1. **Create a new rule as a `.txt` file** in the `rules/` directory.
2. **YAML frontmatter** (required fields only):
   ```yaml
   ---
   description: "Clear, actionable summary of the rule."
   globs:
     - "glob/pattern/for/applicability"
   ---
   ```
3. **Validate** the rule file for correct frontmatter and content.
4. **Rename/move** the file to `.mdc` extension once validated.
5. **Bulk import/export** is supported via the admin UI and CLI.
6. **References:** See [cursor_rules.mdc](mdc:.cursor/rules/cursor_rules.mdc) for formatting.

---

## 🧪 Testing & Environment

- **Test environment setup:**
  ```sh
  make -f Makefile.ai test-setup
  ```
- **Test workflow:**
  1. `make -f Makefile.ai ai-env-up`
  2. `make -f Makefile.ai ai-test PYTEST_ARGS="-x"`
  3. `make -f Makefile.ai ai-env-down`
- **Environment variables (test):**
  ```env
  ENVIRONMENT=test
  POSTGRES_HOST=db-test
  POSTGRES_PORT=5432
  REDIS_HOST=redis-test
  REDIS_PORT=6379
  ```

---

## 🗂️ Database & Migrations

- **Use Alembic for all migrations.**
- **Reset DB and re-import as needed for schema changes.**
- **Backup and import scripts handle schema differences and fill missing columns with defaults.**

---

## 🖥️ API & Frontend Integration

- **Admin UI uses the correct API base URL via Docker Compose and build args.**
- **Endpoints and UI for bug reporting, enhancement suggestions, and proposal management are available.**
- **Enhancements can be transferred to proposals or rejected via API and UI.**

---

## 🐞 Bug Reporting & Enhancements

- **Report bugs and suggest enhancements via:**
  - `/bug-report` endpoint
  - `/suggest-enhancement` endpoint
  - Admin UI
- **Status updates and transfers are supported in real time.**

---

## 📚 Best Practices

- **Always use Makefile.ai for automation.**
- **Keep rule frontmatter minimal (`description`, `globs`).**
- **Document all new rules and workflows.**
- **Use Docker service names and internal ports.**
- **Never mix test and dev environments.**
- **Update documentation and onboarding guides as workflows evolve.**

---

## 🧑‍💻 Onboarding Checklist

- [ ] Read and understand this onboarding guide.
- [ ] Use Makefile.ai for all automation.
- [ ] Follow rule file creation and validation steps.
- [ ] Use admin UI or CLI for rule, bug, and enhancement management.
- [ ] Keep all configs and ports consistent.
- [ ] Ask for help or clarification if needed.

---

## 📖 References

- [8-Step Guide to Creating a Prompt for AI (TeamAI)](https://teamai.com/blog/prompt-libraries/8-step-guide-to-creating-a-prompt-for-ai/)
- [Create Onboarding Documents FASTER with AI (OmniGPT)](https://www.linkedin.com/pulse/create-onboarding-documents-faster-ai-ultimate-prompt-every-project-vp0uc)
- [cursor_rules.mdc](mdc:.cursor/rules/cursor_rules.mdc)
- [pytest_execution.mdc](mdc:.cursor/rules/pytest_execution.mdc)
- [testing_flow.mdc](mdc:.cursor/rules/testing_flow.mdc)
- [GitHub Markdown Syntax Guide](https://docs.github.com/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)

---

> _Tip: You can use this document as a system prompt, onboarding doc, or preamble for new agents or users. The more context you provide, the better the results—see [TeamAI's prompt engineering guide](https://teamai.com/blog/prompt-libraries/8-step-guide-to-creating-a-prompt-for-ai/) for more tips._

---

## 🛡️ Database Backup, Restore, and Nuke (NEW)

**Backup the database:**
```bash
make -f Makefile.ai ai-db-backup
# or data-only:
make -f Makefile.ai ai-db-backup-data-only
```
Creates a timestamped SQL file in `backups/`.

**Restore the database:**
```bash
make -f Makefile.ai ai-db-restore BACKUP=backups/rulesdb-YYYYMMDD-HHMMSS.sql
# or data-only:
make -f Makefile.ai ai-db-restore-data BACKUP=backups/rulesdb-data-YYYYMMDD-HHMMSS.sql
```

**Nuke the database (danger!):**
```bash
make -f Makefile.ai ai-db-nuke
```
This will delete ALL Postgres data and volumes, then re-run migrations.

**Troubleshooting:**
- If you see enum or duplicate key errors on restore, ensure your schema matches the backup and use data-only restore if needed.
- Always use internal Docker service names and ports (e.g., `db-test:5432`).

---

## 🌍 Portable Rules Import/Export (NEW)

**Propose a portable rule:**
```bash
make -f Makefile.ai ai-propose-portable-rule \
  RULE_TYPE=formatting \
  DESCRIPTION='All .mdc files must have frontmatter' \
  DIFF='---\ndescription: ...\nglobs: ...\n---' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"formatting","cursor","portable"' \
  TAGS='"formatting","cursor","portable"' \
  PROJECT=portable-rules
```

**Batch import portable rules:**
```bash
bash scripts/batch_import_portable_rules.sh
```

---

## 📋 Viewing Logs (NEW)

Use these Makefile.ai targets to view logs for troubleshooting:

- **All containers:**
  ```bash
  make -f Makefile.ai logs
  ```
  Shows the last 100 lines for API, db-test, and frontend containers.

- **API only:**
  ```bash
  make -f Makefile.ai logs-api
  ```

- **Database only:**
  ```bash
  make -f Makefile.ai logs-db
  ```

---

## 🔑 Makefile.ai Target Reference (Updated)

| Target                        | Description                                    |
|-------------------------------|------------------------------------------------|
| ai-test, ai-test-one, ai-test-json | Run tests (all, one, or JSON output)      |
| ai-db-migrate, ai-db-autorevision  | Run/apply DB migrations                   |
| ai-db-backup, ai-db-backup-data-only | Backup DB (full/data-only)              |
| ai-db-restore, ai-db-restore-data   | Restore DB (full/data-only)              |
| ai-db-nuke, ai-db-drop-recreate     | Nuke or reset DB (danger!)               |
| ai-propose-portable-rule            | Propose a portable rule                  |
| ai-approve-all-pending              | Approve all pending proposals            |
| ai-up, ai-down, ai-build, ai-rebuild-all | Start/stop/build/rebuild services   |
| ai-list-rules, ai-list-rules-mdc    | List rules (JSON/MDC)                    |
| ai-onboarding-health                | Run onboarding health check              |
| logs, logs-api, logs-db             | View logs for all, API, or DB containers |

See `Makefile.ai` for the full list and usage examples.

---

## 📌 Port Usage (Reminder)
- **Default API port:** `9103` (update all configs, docs, and clients accordingly)
- **Frontend port:** `3000` (or as set by `ADMIN_FRONTEND_PORT`)
- Always use Docker service names and internal ports for all connections.

---

## 📖 References

- [8-Step Guide to Creating a Prompt for AI (TeamAI)](https://teamai.com/blog/prompt-libraries/8-step-guide-to-creating-a-prompt-for-ai/)
- [Create Onboarding Documents FASTER with AI (OmniGPT)](https://www.linkedin.com/pulse/create-onboarding-documents-faster-ai-ultimate-prompt-every-project-vp0uc)
- [cursor_rules.mdc](mdc:.cursor/rules/cursor_rules.mdc)
- [pytest_execution.mdc](mdc:.cursor/rules/pytest_execution.mdc)
- [testing_flow.mdc](mdc:.cursor/rules/testing_flow.mdc)
- [GitHub Markdown Syntax Guide](https://docs.github.com/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)

---

> _Tip: You can use this document as a system prompt, onboarding doc, or preamble for new agents or users. The more context you provide, the better the results—see [TeamAI's prompt engineering guide](https://teamai.com/blog/prompt-libraries/8-step-guide-to-creating-a-prompt-for-ai/) for more tips._

---

## 📝 Example: Fetching and Writing Rules to .mdc File

Below is a robust example of how to fetch rules from the central server and write them to a `.mdc` file, ensuring no placeholders are left in the output.

### Python Script Example

```python
import requests
import json
import os

# Config
RULE_API_URL = os.environ.get("RULE_API_URL", "http://localhost:9103/rules")
OUTPUT_PATH = ".cursor/rules/rules.mdc"

# Fetch rules from the API
response = requests.get(RULE_API_URL)
response.raise_for_status()
rules = response.json()

# Format as pretty JSON
rules_json = json.dumps(rules, indent=2)

# Write to .mdc file with required frontmatter
with open(OUTPUT_PATH, "w") as f:
    f.write("---\n")
    f.write('description: "Fetched rules from the central rule server"\n')
    f.write("globs:\n  - .cursor/rules/rules.mdc\n")
    f.write("---\n\n")
    f.write("```json\n")
    f.write(rules_json)
    f.write("\n```")

print(f"Wrote {len(rules)} rules to {OUTPUT_PATH}")
```

### Shell Script Example (curl + jq)

```bash
#!/bin/bash
API_URL="${RULE_API_URL:-http://localhost:9103/rules}"
OUTPUT=".cursor/rules/rules.mdc"

echo "---" > "$OUTPUT"
echo 'description: "Fetched rules from the central rule server"' >> "$OUTPUT"
echo "globs:" >> "$OUTPUT"
echo "  - .cursor/rules/rules.mdc" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"
echo '```json' >> "$OUTPUT"
curl -s "$API_URL" | jq '.' >> "$OUTPUT"
echo '```' >> "$OUTPUT"

echo "Wrote rules to $OUTPUT"
```

### Validation Step (Recommended)

After writing the file, you can add a check to ensure the code block contains valid JSON and not a placeholder:

```python
with open(OUTPUT_PATH) as f:
    content = f.read()
    if "[REPLACE_WITH_JSON_ARRAY]" in content:
        raise ValueError("Placeholder found! The rules JSON was not inserted correctly.")
```

**Best Practices:**
- Never leave a placeholder in the final `.mdc` file.
- Always check that the code block contains valid JSON.
- Reference this script as the standard for rule syncing in all IDEs/agents. 

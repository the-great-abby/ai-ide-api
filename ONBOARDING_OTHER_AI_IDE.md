# Onboarding Another AI-IDE

## 🔑 API Token Onboarding & Error Log Lookup

**New!** You can now generate your own API access token for secure integration and troubleshooting.

- **Generate a token:**  
  `POST /admin/generate-token`  
  Include a description and (optionally) your agent name. The API will return a new token—store it securely!

- **Use your token:**  
  For any protected endpoint (such as error log lookup), include:  
  `Authorization: Bearer <your-token>`

- **Look up error details:**  
  When the API returns an error with a reference ID (for both 500 and 422 errors), you can fetch details:  
  `GET /admin/errors/{error_id}` (requires your token)

- **Step-by-step example:**
  1. **Trigger a 422 validation error** (e.g., by submitting an invalid payload):
     ```bash
     curl -X POST http://localhost:9103/memory/nodes \
       -H "Content-Type: application/json" \
       -d '{"namespace": "test", "content": "Should fail", "embedding": null, "metadata": null}'
     # Response:
     # {
     #   "detail": [...],
     #   "body": {...},
     #   "path": "/memory/nodes",
     #   "message": "Validation failed. Please check your input and try again.",
     #   "error_id": "<error_id>"
     # }
     ```
  2. **Look up the error details** using your onboarding token:
     ```bash
     curl -H "Authorization: Bearer <your-token>" http://localhost:9103/admin/errors/<error_id>
     # Response includes timestamp, path, message, and stack trace
     ```
  3. **You can also look up 500 errors** in the same way (see example above).

- **Best practices:**  
  - Treat tokens like passwords—never share or commit them.  
  - Revoke tokens if compromised or no longer needed.  
  - See the full user story: [`docs/user_stories/api_token_onboarding.md`](docs/user_stories/api_token_onboarding.md)

This enables self-service onboarding, secure access, and easier debugging for all AI IDEs and agents.

Welcome! This document is your comprehensive onboarding guide for integrating another AI IDE or agent into the AI-IDE API project. Please follow these steps to ensure seamless collaboration, automation, and rule management.

# 🧠 AI Memory Graph API: Semantic Memory for Your AI IDE

> **Integration Note (2025-05-17):**
> 
> The memory graph API now guarantees that all `embedding` fields are returned as proper lists (not strings), regardless of how they are stored in the database. This resolves previous FastAPI validation errors and ensures compatibility with all AI IDE clients. If you previously encountered issues with embedding serialization, update your client to expect a list. See the user story [`docs/user_stories/ai_memory_vector_sqlalchemy_limitations.md`](docs/user_stories/ai_memory_vector_sqlalchemy_limitations.md) for background and [`rule_api_server.py`](rule_api_server.py) for the backend patch.

> **Integration Note (2025-05-18):**
> 
> The memory graph API now generates all `embedding` fields server-side. Do NOT provide `embedding` in POST /memory/nodes requests; the backend will generate and return the embedding automatically. If you previously provided `embedding` in your payloads, update your client to omit it.

**New Feature!** The AI-IDE API now supports a powerful memory graph API for storing, relating, and searching ideas, notes, and code snippets using semantic embeddings and explicit relationships.

- **What is it?**
  - A set of API endpoints for storing and relating knowledge as a graph (nodes and edges), with support for vector search (semantic similarity).
  - Enables your AI IDE to remember, relate, and retrieve information across sessions, projects, and users.

- **Why use it?**
  - Build context-aware assistants, code reviewers, or knowledge explorers.
  - Store and traverse ideas, notes, and code with semantic search and explicit relationships.
  - Share and query knowledge across multiple AI IDEs or agents.

- **How to use it?**
  - See the user story: [`docs/user_stories/ai_memory_graph_api.md`](docs/user_stories/ai_memory_graph_api.md)
  - Try the endpoints: `/memory/nodes`, `/memory/edges`, `/memory/nodes/search`
  - Example curl command to add a node:
    ```bash
    curl -X POST http://localhost:9103/memory/nodes \
      -H "Content-Type: application/json" \
      -d '{
        "namespace": "notes",
        "content": "This is an idea about AI memory.",
        "meta": "{\"tags\": [\"ai\", \"memory\"]}"
      }'
    ```
  - List all nodes:
    ```bash
    curl http://localhost:9103/memory/nodes
    ```
  - Full details and best practices: [`docs/user_stories/ai_memory_graph_api.md`](docs/user_stories/ai_memory_graph_api.md)

> **Tip:** You can discover all available endpoints (including memory features) by fetching the OpenAPI schema:
> - Visit [http://localhost:9103/docs](http://localhost:9103/docs) in your browser
> - Or run: `make -f Makefile.ai ai-docs`

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
>    - [https://github.com/the-great-abby/ai-ide-api/blob/main/ONBOARDING_OTHER_AI_IDE.md](https://github.com/the-great-abby/ai-ide-api/blob/main/ONBOARDING_OTHER_AI_IDE.md)
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

---

## 🗂️ Centralized Rule Index for AI-IDE Agents

### Quick Start for AI-IDE Agents

> **Copy and use this as your initial onboarding prompt:**
>
> 1. Fetch all rules from `http://<your-api-host>:9103/rules`
> 2. Parse and group by category/tag.
> 3. Generate a Markdown index file (`cursor_rules.md` or `index.md`) listing all rules, grouped and described.
> 4. Always include this index in your context for code review and onboarding.
> 5. Regenerate the index whenever rules change.

### Sample Python Script: Generate a Centralized Rule Index

```python
import requests
from collections import defaultdict

API_URL = 'http://<your-api-host>:9103/rules'  # Update as needed
OUTPUT = 'cursor_rules.md'

# Fetch rules from the API
rules = requests.get(API_URL).json()

# Group rules by category
categories = defaultdict(list)
for rule in rules:
    cats = rule.get('categories') or ['Uncategorized']
    if isinstance(cats, str):
        cats = [cats]
    for cat in cats:
        categories[cat].append(rule)

# Write the Markdown index
with open(OUTPUT, 'w') as f:
    f.write('# Centralized Rule Index\n\n')
    f.write('This file is auto-generated from the API.\n\n')
    # Table of contents
    f.write('## Table of Contents\n')
    for cat in sorted(categories):
        f.write(f'- [{cat}](#{cat.lower().replace(" ", "-")})\n')
    f.write('\n')
    # Rules by category
    for cat in sorted(categories):
        f.write(f'\n## {cat}\n')
        for rule in categories[cat]:
            f.write(f'\n### {rule.get("description", "(No description)")}\n')
            f.write(f'- **ID:** `{rule.get("id", "")}`\n')
            f.write(f'- **Categories:** {", ".join(rule.get("categories", []))}\n')
            f.write(f'- **Tags:** {", ".join(rule.get("tags", []))}\n')
            if rule.get('user_story'):
                f.write(f'- **User Story:** {rule["user_story"]}\n')
            if rule.get('examples'):
                f.write(f'- **Example:**\n\n    {rule["examples"]}\n')
            f.write('\n')
print(f'Wrote {OUTPUT} with {len(rules)} rules grouped by {len(categories)} categories.')
```

This script will:
- Fetch all rules from your API
- Group them by category
- Write a Markdown file with a table of contents, category sections, and details for each rule
- Include description, categories, tags, user story, and example usage if present

---

## 🚀 Quick Start: Accessing API Documentation (OpenAPI)

To help you get started quickly with the API, you can fetch the latest OpenAPI documentation using the provided Makefile target. This is the recommended way for both humans and AI IDEs to discover and interact with the API.

**Fetch the OpenAPI docs with one command:**

```bash
make -f Makefile.ai ai-docs
```

- This will print the OpenAPI documentation endpoint or return the docs directly if the API is running.
- Alternatively, you can visit the interactive docs in your browser:
  - [http://localhost:9103/docs](http://localhost:9103/docs)

**Why is this important?**
- The OpenAPI docs describe all available API endpoints, request/response formats, and authentication details.
- Many tools (including AI IDEs) can use this to auto-generate clients, test endpoints, or explore the API interactively.

**Troubleshooting:**
- If the API is not running, start it with:
  ```bash
  make -f Makefile.ai ai-up
  ```
- If you need more help, see the full user story in `docs/user_stories/openapi_docs_onboarding.md` (if available).

---

## 🧠 Memory Graph Quickstart: Ready-to-Run Scripts

The following scripts help you interact with the memory graph API for onboarding, testing, and automation.

### Add a memory node
```bash
curl -X POST http://localhost:9103/memory/nodes \
  -H "Content-Type: application/json" \
  -d '{"namespace": "notes", "content": "Example node", "meta": "{\"tags\": [\"example\"]}"}'
```

### Add an edge
```bash
curl -X POST http://localhost:9103/memory/edges \
  -H "Content-Type: application/json" \
  -d '{"from_id": "NODE1_ID", "to_id": "NODE2_ID", "relation_type": "related_to", "meta": "{\"note\": \"Example edge\"}"}'
```

### List all nodes
```bash
curl http://localhost:9103/memory/nodes | jq .
```

### List all edges
```bash
curl http://localhost:9103/memory/edges | jq .
```

### Single-hop traversal (direct neighbors)
```bash
NODE_ID="YOUR_NODE_ID"
for to_id in $(curl -s "http://localhost:9103/memory/edges?from_id=$NODE_ID" | jq -r '.[].to_id'); do
  curl -s http://localhost:9103/memory/nodes | jq --arg id "$to_id" '.[] | select(.id == $id)'
done
```

### Multi-hop (recursive) traversal
```bash
#!/bin/bash
START_NODE="YOUR_NODE_ID"
declare -A visited
traverse() {
  local node_id="$1"
  if [[ -n "${visited[$node_id]}" ]]; then return; fi
  visited[$node_id]=1
  echo "Node: $node_id"
  curl -s http://localhost:9103/memory/nodes | jq --arg id "$node_id" '.[] | select(.id == $id)'
  for to_id in $(curl -s "http://localhost:9103/memory/edges?from_id=$node_id" | jq -r '.[].to_id'); do
    traverse "$to_id"
  done
}
traverse "$START_NODE"
```

### Filter by relation type
```bash
REL_TYPE="related_to"
NODE_ID="YOUR_NODE_ID"
for to_id in $(curl -s "http://localhost:9103/memory/edges?from_id=$NODE_ID&relation_type=$REL_TYPE" | jq -r '.[].to_id'); do
  curl -s http://localhost:9103/memory/nodes | jq --arg id "$to_id" '.[] | select(.id == $id)'
done
```

### Export to DOT/Graphviz
```bash
echo "digraph MemoryGraph {"
curl -s http://localhost:9103/memory/edges | jq -r '.[] | "\"\(.from_id)\" -> \"\(.to_id)\" [label=\"\(.relation_type)\"] ;"'
echo "}"
```
Then render with:
```bash
dot -Tpng graph.dot -o graph.png
```

---

**See [`docs/user_stories/ai_memory_graph_api.md`](docs/user_stories/ai_memory_graph_api.md) for full details and best practices.**

---

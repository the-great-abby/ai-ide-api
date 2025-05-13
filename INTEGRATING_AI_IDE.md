# Integrating an AI-IDE with the Rule API

> **Note:** The default API server port is **9103**. Update your URLs accordingly.

---

## Step-by-Step Integration

1. **Set Up Your Project**
   - Ensure your AI-IDE project has a `.cursor/rules/` directory.

2. **Use This Example Prompt**
   Copy and paste the following prompt to your AI-IDE:

   ```
   I want to configure this AI-IDE to automatically fetch and sync rules from our central rule server at http://localhost:9103 (or your actual server URL). Please generate a Cursor rule in .mdc (Markdown Cursor) format that will:
   - Use the /rules endpoint to fetch all approved rules
   - Save the results to a local file (e.g., rules.mdc)
   - (Optional) Support filtering by category or tag
   - Be easy to run or schedule for periodic updates

   **Due to a known Cursor bug, first create a plain text file (e.g., fetch_remote_rules.txt) with the rule content, then move or copy it to .cursor/rules/ and rename it to fetch_remote_rules.mdc.**

   **The .mdc file MUST include frontmatter with at least these fields:**
   ---
   description: Fetch all approved rules from the API
   globs: "**/*"
   ---
   (rest of the rule...)

   Show me the .mdc config file and explain how to use it.
   ```

   Example content for `fetch_remote_rules.txt`:
   ```mdc
   ---
   description: Fetch all approved rules from the API
   globs: "**/*"
   ---
   type: http
   url: http://localhost:9103/rules
   method: GET
   output: rules.mdc
   ```

   > **Don't Forget:**
   > - The content between the `---` lines (frontmatter) is required and must not be removed or altered.
   > - After creating the file, verify it contains the full frontmatter block.
   > - Adjust the URL or output filename as needed for your environment.

3. **Reference the Rule File**
   - Reference this `.mdc` file in your project documentation and rule set as the standard way to fetch and sync rules.

---

(Continue with any additional integration steps as needed)

---

## Getting Started: User Story

> **As a developer integrating a new AI-IDE with the Rule Management System, I want to configure my AI-IDE to automatically pull rulesets and proposals from the central server, so that my IDE can provide up-to-date guidance and enforce best practices.**

### Step-by-Step Onboarding

1. **Configure the AI-IDE to Point to the Rule Server**
   - Set the API base URL (e.g., `AI_IDE_API_URL=http://your-server:9103`).
   - (If required) Add authentication credentials.

2. **Create Cursor Rules for Remote Fetching**
   - In your AI-IDE's configuration, define a rule or plugin that fetches rules from the `/rules` endpoint.
   - Example (`.cursor/rules/fetch_remote_rules.mdc`):
     ```mdc
     ---
     name: fetch_remote_rules
     type: http
     url: ${AI_IDE_API_URL}/rules
     method: GET
     output: rules.mdc
     ---
     ```
   - (Adjust the URL or output filename as needed for your environment.)

   > **Don't Forget: Save and Reference the Rule Creation File**
   >
   > After generating your `.mdc` rule config, **save it as a local file** in your `.cursor/rules/` directory (e.g., `fetch_remote_rules.mdc`).
   > If your AI-IDE does not create the file automatically, copy the example content and create the file manually.
   >
   > **Reference this file** in your project documentation and rule set as the standard way to fetch and sync rules.

3. **(Optional) Set Up Automated Sync**
   - Schedule the AI-IDE to periodically refresh rules from the server.

4. **Test the Integration**
   - Run the fetch command or trigger the rule.
   - Verify that rules are downloaded and available in the IDE.

5. **Troubleshoot**
   - If you see errors, check the Troubleshooting section below.

---

## Prompting Your AI-IDE to Generate Cursor Rules

*This section has moved! For human-friendly, step-by-step instructions on prompting your AI-IDE to generate Cursor rules/config files for syncing with the rule server, see [ONBOARDING_OTHER_AI_IDE.md](./ONBOARDING_OTHER_AI_IDE.md).*

---

Why This Matters
----------------
- **Centralized Best Practices:** Ensures all AI-IDEs use the latest, approved rules.
- **Easy Updates:** New rules or changes are automatically distributed.
- **Consistency:** All users and tools are aligned with the same standards.

---

## Overview

The Rule Management System exposes a RESTful API for:
- Fetching approved rules (with versioning, categories, and tags)
- Submitting and managing rule proposals
- Accessing rule version history
- Filtering rules by category/tag

All endpoints are documented in the OpenAPI schema (`/docs` or `/openapi.json`).

---

## API Endpoints

| Endpoint                              | Method | Description                                 |
|---------------------------------------|--------|---------------------------------------------|
| `/rules`                              | GET    | List all approved rules (filterable)        |
| `/rules/{rule_id}`                    | GET    | Get a specific rule by ID                   |
| `/rules/{rule_id}/history`            | GET    | Get version history for a rule              |
| `/proposals`                          | GET    | List all pending proposals                  |
| `/proposals`                          | POST   | Submit a new rule proposal                  |
| `/proposals/{proposal_id}/approve`    | POST   | Approve a proposal (if authorized)          |
| `/proposals/{proposal_id}/reject`     | POST   | Reject a proposal (if authorized)           |

See the OpenAPI docs for full details and request/response schemas.

---

## Authentication

- **Default:** No authentication required for read-only endpoints (unless configured otherwise).
- **Write/Approval:** If enabled, use API keys or OAuth. (Contact admin for credentials.)

---

## Environment & Configuration

- **API Base URL:** Set the base URL for the backend API (e.g., `http://localhost:9103` or as provided).
- **CORS:** Enabled for browser-based clients.
- **Environment Variables:**
  - `AI_IDE_API_URL` (recommended for client config)

---

## Rule Format & Versioning

A rule object returned from the API looks like:

```json
{
  "id": "rule_123",
  "content": "Rule text...",
  "version": 3,
  "categories": ["pytest", "testing"],
  "tags": ["fast", "docker"],
  "created_at": "2024-06-01T12:00:00Z"
}
```
- **Versioning:** Each approval increments the version. Previous versions are accessible via `/rules/{rule_id}/history`.
- **Categories/Tags:** Used for filtering and organization.

---

## Filtering Rules

You can filter rules by category and/or tag:
- `/rules?category=pytest`
- `/rules?tag=docker`
- `/rules?category=pytest&tag=docker`

Multiple values (if supported): `/rules?category=pytest,unit&tag=docker,fast`

---

## Example Requests

### Fetch All Rules (curl)
```sh
curl -X GET "http://localhost:9103/rules"
```

### Fetch Rules by Category and Tag (curl)
```sh
curl -X GET "http://localhost:9103/rules?category=pytest&tag=docker"
```

### Fetch Rule Version History (curl)
```sh
curl -X GET "http://localhost:9103/rules/rule_123/history"
```

### Submit a New Proposal (curl)
```sh
curl -X POST "http://localhost:9103/proposals" \
     -H "Content-Type: application/json" \
     -d '{
           "content": "New rule text...",
           "categories": ["pytest"],
           "tags": ["fast"]
         }'
```

### Fetch All Rules (Python)
```python
import requests

BASE_URL = "http://localhost:9103"
resp = requests.get(f"{BASE_URL}/rules")
rules = resp.json()
print(rules)
```

### Submit a New Proposal (Python)
```python
import requests

BASE_URL = "http://localhost:9103"
proposal = {
    "content": "New rule text...",
    "categories": ["pytest"],
    "tags": ["fast"]
}
resp = requests.post(f"{BASE_URL}/proposals", json=proposal)
print(resp.json())
```

---

## Troubleshooting & Common Issues

- **CORS Errors:** Ensure CORS is enabled on the backend (should be by default).
- **404/422 Errors:** Check endpoint URLs and request payloads for correctness.
- **Authentication Errors:** If API keys are required, include them in headers as instructed.
- **Version Mismatches:** Always fetch the latest rule version before submitting updates.

---

## Further Documentation

- [ONBOARDING.md](./ONBOARDING.md): System architecture, workflows, and environment setup
- [RULES.md](./RULES.md): Rule structure, best practices, and examples
- [OpenAPI Docs](http://localhost:9103/docs): Interactive API documentation

---

**For questions or support, contact the system administrator or open an issue in the repository.**

## Using Makefile.ai for Automation

This project uses a special `Makefile.ai` to standardize all development, testing, and rule management tasks.

**AI-IDE integrations should always invoke tests, migrations, and environment setup via `Makefile.ai` targets, not by running commands directly.**

**Key targets include:**
- `ai-test` — Run all tests in the correct environment
- `ai-test-json` — Run tests with machine-readable output
- `ai-db-migrate` — Run database migrations inside Docker
- `ai-db-revision` — Create new Alembic migrations
- `ai-up` / `ai-down` — Start/stop all services

**Example:**
```sh
make -f Makefile.ai ai-test
make -f Makefile.ai ai-db-migrate
```

> **Why?**
> This ensures all automation is consistent, reproducible, and works in both human and AI-driven workflows.
> See [ONBOARDING.md](./ONBOARDING.md) for a full list of targets and best practices.

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
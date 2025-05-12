# Onboarding Guide

## 🚨 What's New (June 2024)

- **Expanded Test Coverage:**
  - Full test suite now covers bug reporting, enhancement workflows, proposal/enhancement transfers, and all major endpoints.
  - See the new tests in `tests/test_rule_api_server.py` for examples.
- **New API Endpoints:**
  - `/bug-report`, `/suggest-enhancement`, `/enhancements`, `/enhancement-to-proposal/{id}`
  - `/reject-enhancement/{id}`, `/proposal-to-enhancement/{id}`, `/accept-enhancement/{id}`, `/complete-enhancement/{id}`
  - `/changelog` (Markdown changelog for humans/UIs)
  - `/changelog.json` (Structured changelog for programmatic access)
- **Enhancement & Bug Workflow:**
  - Submit, accept, complete, transfer, and reject enhancements via API or UI.
  - Bug reports and enhancements are now first-class citizens in the workflow.
- **Rule Versioning:**
  - Proposals can now reference `rule_id` for updates; rule version history is accessible via `/rules/{rule_id}/history`.
  - **Changelog endpoints:** `/changelog` returns the Markdown changelog for UI/human consumption, `/changelog.json` returns a structured JSON changelog for automation and bots.
- **Makefile.ai Targets:**
  - New targets for enhancements, bug reports, migrations, and DB management.
- **Onboarding & Integration:**
  - Improved onboarding for AI IDEs and automation. See `ONBOARDING_OTHER_AI_IDE.md` and `INTEGRATING_AI_IDE.md`.
- **Best Practices:**
  - Always use Makefile.ai, Docker service names, and internal ports. Keep docs up to date as workflows evolve.

---

## 👋 Welcome!

Welcome to the Rule Proposal API project! We're excited to have you here. This project is about making AI a first-class citizen in the development process—enabling both humans and AI to propose, review, and improve rules together. We value collaboration, learning, and continuous improvement. If you're new, don't hesitate to ask questions or suggest changes—your fresh perspective is valuable!

## Why This Project?
- To create a self-improving, human-reviewed rule management system.
- To make onboarding, testing, and rule evolution easy and transparent.
- To foster a collaborative environment between humans and AI.

---

## ✅ Quick Start Checklist

- [ ] Clone the repo: `git clone <repo-url>`
- [ ] Enter the project directory: `cd <project-dir>`
- [ ] Build Docker images: `make build`
- [ ] **Start the dev server (preferred):** `make up` (or `make up PORT=9001` to use a custom port)
- [ ] Visit the API docs: [http://localhost:8000/docs](http://localhost:8000/docs) (replace 8000 with your chosen port)
- [ ] Run the tests: `make test` (human readable) or `make test-json` (AI/automation friendly)
- [ ] Run a specific test: `make test-one TEST=test_rule_api_server.py::test_docs_endpoint`
- [ ] Run the coverage report: `make coverage`
- [ ] Propose a test rule via the API docs (see below!)
- [ ] **Stop containers:** `make down`

> **Note:** The default API server port for this project is **9103** (not 8000). Update your client, integration, and rule config URLs accordingly.

> **Note:** The API will be available at [http://localhost:<PORT>](http://localhost:<PORT>) when using `make up` or `make up PORT=9001`.

---

## 🏗️ Architecture Overview (Updated)

This project uses a split architecture with Docker Compose:

- **FastAPI Backend** (`api`):
  - Serves the Rule Proposal API (CRUD for rules, proposals, etc.)
  - Runs on port 8000 (configurable via `PORT`)
- **React Admin Frontend** (`frontend`):
  - Modern admin UI for reviewing, approving, and rejecting rule proposals
  - Built with Vite/React, served by nginx
  - Runs on port 3000 by default (configurable via `ADMIN_FRONTEND_PORT`)
- **Docker Compose** orchestrates both services for local dev and deployment
- **Postgres Database** (`rules-postgres`):
  - Stores all rules, proposals, enhancements, and feedback
  - Runs in a Docker container for portability and consistency

> **Note:** As of June 2024, the project has migrated from SQLite to Postgres for improved scalability and reliability. See CHANGELOG.md for details.

### MermaidJS Architecture Diagram
```mermaid
graph TD
  User[User or Admin]
  DB[rules-postgres (Postgres)]

  subgraph Frontend
    FE[Admin Frontend - React]
  end

  subgraph Backend
    BE[API Backend - FastAPI]
  end

  User -->|Web Browser| FE
  FE -->|HTTP API calls| BE
  BE -->|DB access| DB
```

### Service Ports
- **Frontend:** http://localhost:3000 (or your chosen `ADMIN_FRONTEND_PORT`)
- **Backend:** http://localhost:8000 (or your chosen `PORT`)

### How They Communicate
- The frontend makes API requests to the backend (default: `http://localhost:8000`)
- CORS is enabled in FastAPI for local development
- Both services can be started/stopped together with:
  ```bash
  ADMIN_FRONTEND_PORT=4000 make -f Makefile.ai ai-up
  ```

---

## ⚙️ Environment Variable Configuration (Source of Truth)

- **Environment variables** are the source of truth for configuration (e.g., API host, port).
- The `.env` file is used **only for Docker Compose variable substitution** in local development. It is **not** loaded by the app at runtime.
- In production, set environment variables directly (in Compose, Kubernetes, or the host environment).

### Example: Setting Variables in Docker Compose
In `docker-compose.yml`:
```yaml
environment:
  - RULE_API_HOST=${RULE_API_HOST:-localhost}
  - RULE_API_PORT=${RULE_API_PORT:-8000}
```

Or set them in your shell before running Compose:
```bash
export RULE_API_HOST=localhost
export RULE_API_PORT=9001
make up
```

### Example: Setting Variables in Production
- Set environment variables in your deployment system (e.g., Docker Compose, Kubernetes, or directly on the host).
- Do **not** rely on `.env` files or `python-dotenv` in production containers.

---

## 🤖 AI/Automation Friendly Testing

- **Machine-readable test output:**
  - Run `make test-json` to execute tests and output results as `pytest-report.json` (great for AI agents or CI parsing).
  - Example:
    ```bash
    make test-json
    # Output: pytest-report.json
    ```
- **Run a specific test or file:**
  - Use `make test-one TEST=<test_path_or_name>` to run a single test or file.
  - Example:
    ```bash
    make test-one TEST=test_rule_api_server.py::test_docs_endpoint
    ```
- **Human-readable output:**
  - Use `make test` for standard pytest output.

---

## 🛠️ Common Pitfalls & Troubleshooting
- **Docker not running?** Make sure Docker Desktop is started.
- **Port in use?** Use a different port: `make up PORT=9001` or `make up-detached PORT=9002`.
- **File permission errors?** Try running `sudo chown -R $USER:$USER .` in the project directory.
- **Tests not running?** Make sure you're using `make test` (not running pytest directly).
- **Still stuck?** See the next section!

---

## 💬 How to Get Help
- Ask in your team chat (Slack/Discord/etc.)
- Open a GitHub Issue
- Reach out to your onboarding buddy or project maintainer
- Don't be shy—everyone was new once!

---

## 🚀 First Contribution Guide
- Try proposing a sample rule using the API docs (`/propose-rule-change` endpoint)
- Add or improve a test in `test_rule_api_server.py`
- Suggest a doc update if you spot something unclear
- Ask for a pairing session if you want to learn the workflow hands-on

---

## 📝 Rule Proposal Template
When proposing a rule, use this example in the API docs or as a JSON payload:
```json
{
  "rule_type": "pytest_execution",
  "description": "All pytest runs must use Makefile.ai.",
  "diff": "Add rule: Use Makefile.ai for pytest.",
  "submitted_by": "your-name"
}
```

---

## 🔄 Ongoing Improvements
- Please update this doc as the project evolves!
- Add new onboarding tips, gotchas, or workflow changes here.
- Suggest improvements to the workflow, rules, or documentation.
- After your first week, let us know what could be clearer or easier!

---

## Debugging: Environment Detection

The API provides a `/env` endpoint to help you determine which environment (test, production, etc.) the server is running in.

- **Endpoint:** `GET /env`
- **Description:** Returns the current environment as set by the `ENVIRONMENT` environment variable (defaults to `production`).
- **Example Response:**
  ```json
  { "environment": "test" }
  ```
- **Example Usage:**
  ```bash
  curl http://localhost:8000/env
  ```

This is useful for debugging, CI, and AI-IDE integration.

---

## External AI-IDE Communication Flow

External AI-IDEs or clients can interact with the Rule API to propose new rules or fetch existing rules. This diagram shows the flow for both operations:

```mermaid
graph TD
  AIIDE[Other AI-IDE or Client]
  API[API Backend - FastAPI]
  DB[rules-postgres (Postgres)]

  AIIDE -- "POST /propose-rule-change" --> API
  AIIDE -- "GET /rules or /rules-mdc" --> API
  API -- "DB access" --> DB
```

Welcome aboard! If you have questions, open an issue or ask a teammate. We're glad you're here. 🚀 

---

## Workflows

This section documents key automated workflows for development, testing, and rule management. Use these commands and patterns to keep your workflow efficient and consistent.

### 1. Run All Tests
**What:** Run the full test suite in Docker.

**How:**
```bash
make -f Makefile.ai ai-test
```
**When:** Before pushing code, after major changes, or to verify a clean state.

**Troubleshooting:**
- Ensure Docker is running and containers are up.
- If tests fail, check logs and use `make -f Makefile.ai ai-test-json` for machine-readable output.

---

### 2. Lint All Code
**What:** Lint the codebase for style and errors.

**How:**
```bash
make -f Makefile.ai ai-lint-rules
```
**When:** Before PRs, after editing rules, or to enforce style.

**Troubleshooting:**
- Fix any errors or warnings shown in the output.

---

### 3. Approve All Pending Proposals
**What:** Approve every rule proposal currently marked as pending.

**How:**
```bash
make -f Makefile.ai ai-approve-all-pending
```
**When:** After reviewing proposals, or to batch-approve after a bulk import.

**Troubleshooting:**
- Ensure the API is running and the database is accessible.
- If you see errors, check the logs or try `make -f Makefile.ai ai-scan-db` to inspect the DB state.

---

### 4. Environment Management
**What:** Start or stop all services (backend, frontend) with Docker Compose.

**How:**
```bash
ADMIN_FRONTEND_PORT=4000 make -f Makefile.ai ai-up   # Start all services
make -f Makefile.ai ai-down                          # Stop all services
```
**When:** At the start/end of a dev session, or to reset the environment.

**Troubleshooting:**
- If a port is in use, change the port variable (e.g., `ADMIN_FRONTEND_PORT=4001`).
- Use `make -f Makefile.ai ai-status` to check running containers.

---

## API Endpoints (Expanded)

| Endpoint                                 | Method | Description                                 |
|------------------------------------------|--------|---------------------------------------------|
| `/rules`                                 | GET    | List all approved rules (filterable)        |
| `/rules/{rule_id}`                       | GET    | Get a specific rule by ID                   |
| `/rules/{rule_id}/history`               | GET    | Get version history for a rule              |
| `/propose-rule-change`                   | POST   | Submit a new rule proposal                  |
| `/approve-rule-change/{proposal_id}`     | POST   | Approve a proposal                          |
| `/reject-rule-change/{proposal_id}`      | POST   | Reject a proposal                           |
| `/bug-report`                            | POST   | Submit a bug report                         |
| `/suggest-enhancement`                   | POST   | Suggest an enhancement                      |
| `/enhancements`                          | GET    | List all enhancements                       |
| `/enhancement-to-proposal/{id}`          | POST   | Transfer enhancement to proposal            |
| `/reject-enhancement/{id}`               | POST   | Reject an enhancement                       |
| `/proposal-to-enhancement/{id}`          | POST   | Revert proposal to enhancement              |
| `/accept-enhancement/{id}`               | POST   | Accept an enhancement                       |
| `/complete-enhancement/{id}`             | POST   | Complete an enhancement                     |
| `/env`                                   | GET    | Get current environment                     |

See `/docs` for full OpenAPI schema and request/response details.

---

## 🧪 Enhancement & Bug Workflow

- **Submit an enhancement:** `/suggest-enhancement` (API or UI)
- **List enhancements:** `/enhancements`
- **Accept/complete enhancement:** `/accept-enhancement/{id}` → `/complete-enhancement/{id}`
- **Transfer enhancement to proposal:** `/enhancement-to-proposal/{id}`
- **Reject enhancement:** `/reject-enhancement/{id}`
- **Revert proposal to enhancement:** `/proposal-to-enhancement/{id}`
- **Submit a bug report:** `/bug-report`
- **Status transitions:**
  - Enhancement: `open` → `accepted` → `completed` (or `rejected`/`transferred`)
  - Proposal: `pending` → `approved`/`rejected`/`reverted_to_enhancement`

---

## 🧪 Rule Versioning & History

- **Proposals for rule updates** should include a `rule_id` field referencing the rule to update.
- **On approval:** The rule's version is incremented, and the previous version is saved to history.
- **Access history:** `/rules/{rule_id}/history` returns all previous versions and metadata.

---

## 🛠️ Makefile.ai Targets (Expanded)

- `ai-test`, `ai-test-one`, `ai-test-json`: Run tests
- `ai-accept-enhancement`, `ai-complete-enhancement`: Accept/complete enhancements
- `ai-list-enhancements`: List enhancements (optionally by status)
- `ai-proposal-to-enhancement`: Revert proposal to enhancement
- `ai-db-autorevision`, `ai-db-migrate`: DB migrations
- `ai-bug-report`, `ai-suggest-enhancement`: Submit bug/enhancement via CLI
- See `Makefile.ai` for the full list and usage examples

---

## 📚 Best Practices (Updated)
- Always use Makefile.ai for all automation (tests, builds, migrations, DB, etc.)
- Use Docker service names and internal ports for all connections
- Keep rule frontmatter minimal (`description`, `globs`)
- Document new rules, endpoints, and workflows as they evolve
- Keep onboarding and integration docs up to date
- Never mix test and dev environments
- Add/expand tests for new features and workflows

--- 
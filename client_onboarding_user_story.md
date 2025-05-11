# Client Onboarding User Story: Accessing Rules via Docker

## Scenario
You're a developer on a new project. Your team wants to leverage shared best practices and rules, but you don't want to copy files or maintain your own rule logic. Instead, you want to access a central Rule API running in a Docker container, and fetch example rules for your project or AI-IDE to use.

---

## Project Context: Multi-Project Support

The Rule API supports a `project` field for all rules and proposals. This allows you to:
- Propose and track rules specific to each project
- Filter and fetch rules for a given project
- Organize exported rules by project
- Share best practices across projects while allowing for customization

### Proposing a Rule with Project Context
Include a `project` field in your rule proposal:
```json
{
  "rule_type": "pytest_execution",
  "description": "All pytest runs must use Makefile.ai.",
  "diff": "...",
  "submitted_by": "ai-ide",
  "project": "my-cool-app"
}
```

### Fetching Rules for a Specific Project
Use the `project` query parameter:
```bash
curl http://localhost:9001/rules?project=my-cool-app
```
Or for MDC format:
```bash
curl http://localhost:9001/rules-mdc?project=my-cool-app
```

### Suggesting Rules for a Project
Use the `--project` flag with the suggestion script:
```bash
python scripts/suggest_rules.py --project my-cool-app
```
All suggestions will include the `project` field.

---

## Step 1: Run the Rule API (Preferred: Makefile & Docker Compose)

For local development and testing, use the provided Makefile and Docker Compose setup:

```bash
make up                # Default port 8000
make up PORT=9001      # Use a custom port (e.g., 9001)
make up-detached PORT=9002  # Run in background on port 9002
```
- This starts the Rule API server in a container on your chosen port.
- The API will be available at [http://localhost:<PORT>](http://localhost:<PORT>), e.g., http://localhost:9001.

To stop the server and clean up containers:
```bash
make down
```

> **Tip:** Always use `make up` and `make down` for local development and integration. You can override the port with the `PORT` variable.

If you need to run the container manually (e.g., in CI/CD or on a remote server):
```bash
docker run -d --name rule-api -p 8000:8000 your-org/rule-api:latest
```

---

## Step 2: Access Example Rules via the API

Once the container is running, you can fetch the current rules from any project or tool that can make HTTP requests.

### Using Environment Variables for API URL and Port
**Best Practice:**
- **Environment variables** are the source of truth for configuration (e.g., API host, port).
- The `.env` file is used **only for Docker Compose variable substitution** in local development. It is **not** loaded by the app or client code at runtime.
- In production or CI, set environment variables directly (in Compose, Kubernetes, or the host environment).

- `RULE_API_HOST` (default: `localhost`)
- `RULE_API_PORT` (default: `8000`)

### Example: Fetch All Rules with Python
```python
import os
import requests

RULE_API_HOST = os.environ.get("RULE_API_HOST", "localhost")
RULE_API_PORT = os.environ.get("RULE_API_PORT", "8000")
RULE_API_URL = f"http://{RULE_API_HOST}:{RULE_API_PORT}"

rules = requests.get(f"{RULE_API_URL}/rules").json()
print(rules)
```

---

## Step 3: Use the Rules in Your Project or AI-IDE

- Your AI-IDE or linter can fetch the rules at startup or on demand.
- You can propose new rules by POSTing to `/propose-rule-change` (include the `project` field if relevant).
- You can automate rule syncing by running a script or pre-commit hook that fetches `/rules`.

---

## Step 4: Confirm AI-IDE Integration with a Sample Rule Proposal

To confirm your AI-IDE or client can interact with the Rule API, try proposing a sample rule. This will verify end-to-end connectivity and functionality.

### Sample Rule Proposal (JSON)
```json
{
  "rule_type": "ai_integration_test",
  "description": "This is a test rule to confirm AI-IDE integration with the Rule API.",
  "diff": "Add rule: AI-IDE must be able to propose rules via the Rule API.",
  "submitted_by": "ai-ide-integration-test",
  "project": "my-cool-app"
}
```

### Propose the Rule with curl
```bash
curl -X POST http://localhost:9001/propose-rule-change \
  -H "Content-Type: application/json" \
  -d '{
    "rule_type": "ai_integration_test",
    "description": "This is a test rule to confirm AI-IDE integration with the Rule API.",
    "diff": "Add rule: AI-IDE must be able to propose rules via the Rule API.",
    "submitted_by": "ai-ide-integration-test",
    "project": "my-cool-app"
  }'
```

### Propose the Rule with Python
```python
import os
import requests

RULE_API_HOST = os.environ.get("RULE_API_HOST", "localhost")
RULE_API_PORT = os.environ.get("RULE_API_PORT", "9001")  # Use your chosen port
RULE_API_URL = f"http://{RULE_API_HOST}:{RULE_API_PORT}"

payload = {
  "rule_type": "ai_integration_test",
  "description": "This is a test rule to confirm AI-IDE integration with the Rule API.",
  "diff": "Add rule: AI-IDE must be able to propose rules via the Rule API.",
  "submitted_by": "ai-ide-integration-test",
  "project": "my-cool-app"
}

response = requests.post(f"{RULE_API_URL}/propose-rule-change", json=payload)
print(response.status_code, response.json())
```

### Sample Prompt for AI Agent
```
Propose a test rule to the Rule API to confirm integration is working. Use the following JSON payload:
{
  "rule_type": "ai_integration_test",
  "description": "This is a test rule to confirm AI-IDE integration with the Rule API.",
  "diff": "Add rule: AI-IDE must be able to propose rules via the Rule API.",
  "submitted_by": "ai-ide-integration-test",
  "project": "my-cool-app"
}
The Rule API endpoint is http://localhost:9001/propose-rule-change (replace 9001 with your port if different).
```

---

## Step 5: MDC Rule Integration (Markdown Code Format)

If you use the MDC (Markdown Code) format for rules, you can fetch and manage rules in this format as well:

### Fetch All Rules in MDC Format via API
- The Rule API provides a `/rules-mdc` endpoint that returns all rules as a list of MDC-formatted strings (from the `diff` field).
- You can filter by project:
  ```bash
  curl http://localhost:9001/rules-mdc?project=my-cool-app
  ```

**Example Python:**
```python
import os
import requests

RULE_API_HOST = os.environ.get("RULE_API_HOST", "localhost")
RULE_API_PORT = os.environ.get("RULE_API_PORT", "9001")
RULE_API_URL = f"http://{RULE_API_HOST}:{RULE_API_PORT}"

mdc_rules = requests.get(f"{RULE_API_URL}/rules-mdc?project=my-cool-app").json()
for mdc in mdc_rules:
    print(mdc)
```

### Convert All Rules to Individual MDC Files
- Use the provided script to convert `rules.json` to individual `.md` files (one per rule) in a `rules_mdc/` directory, organized by project:

```bash
python scripts/export_approved_rules.py
```
- Each file will be named `<rule_type>_<id>.md` and placed in a subdirectory for its project.

**Tip:** Use MDC files for human-readable documentation, code review, or version control alongside the API/automation workflow.

---

## Tips
- Prefer `make up` and `make down` for local development and integration.
- You can run the Rule API container on any server accessible to your team or CI/CD pipeline.
- Use environment variables or config files in your project to store the Rule API URL and port.
- The API is documented at [http://localhost:<PORT>/docs](http://localhost:<PORT>/docs) when the container is running.

---

**Now your project can always stay up-to-date with the latest rules—no manual copying required!** 
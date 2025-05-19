# User Story: Listing Enhancements via API and Makefile

## Motivation
As a developer, admin, or AI agent, I want a simple, reliable way to list all enhancements (feature suggestions, improvements, etc.) in the system, so that I can review, triage, and act on them efficiently. This should be possible both via the API (for automation and integration) and via a Makefile.ai target (for developer convenience).

---

## Actors
- Developer
- Admin
- AI agent
- CI/CD pipeline

---

## Preconditions
- The API is running and exposes an `/enhancements` endpoint for listing enhancements.
- The Makefile.ai can invoke curl or httpie to call the API.
- (Optional) The frontend or admin UI also lists enhancements for manual review.

---

> **Note:**
> If you are running this command from inside a Docker container, use `host.docker.internal` instead of `localhost` for the API URL. For example: `http://host.docker.internal:9103/enhancements`

---

## Step-by-Step Actions

### 1. List Enhancements via API
```bash
curl http://host.docker.internal:9103/enhancements
```
- Returns a JSON array of all enhancements, including their status, description, and metadata.

### 2. List Enhancements via Makefile.ai Target
- Add a target to `Makefile.ai`:
  ```makefile
  ai-list-enhancements:
  	curl http://host.docker.internal:9103/enhancements | jq
  ```
- Run the target:
  ```bash
  make -f Makefile.ai ai-list-enhancements
  ```
- (Optional) Use `http` or add filtering/formatting as needed.

### 3. (Optional) List Enhancements via Frontend
- Visit the admin or enhancements page in the web UI to view and filter enhancements.

---

## Expected Outcomes
- All enhancements are easily discoverable via API, Makefile, and UI.
- Developers and admins can quickly review and triage enhancements.
- The process is automated and scriptable for integration with bots or CI/CD.

---

## Best Practices
- Keep the API endpoint and Makefile target documented in onboarding and developer docs.
- Use `jq` or similar tools for readable output in the terminal.
- Automate regular listing or reporting of enhancements for team review.
- Ensure enhancements have clear status and metadata for effective triage.

---

## References
- API endpoint: `GET /enhancements`
- Makefile.ai target: `ai-list-enhancements`
- Admin/frontend UI for manual review 
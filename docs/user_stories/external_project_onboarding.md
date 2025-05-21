# User Story: External Project Onboarding via API

## Motivation
As an external project owner or integrator, I want a simple, automated way to initialize and track onboarding progress for my project, so I can ensure all required steps are completed and visible to my team.

---

## Actors
- External project owner
- API integrator
- Automation scripts

---

## Preconditions
- The API is running and accessible
- The onboarding_paths.json file defines the steps for 'external_project'

---

## Step-by-Step Actions
1. **Review onboarding and automation docs:**
   - Download and review the onboarding and automation best practices documentation:
     - `GET /onboarding-docs` (automation and Makefile best practices)
     - `GET /onboarding/user_story/external_project` (this user story)
2. **Call the onboarding initialization endpoint:**
   - Send a POST request to `/onboarding/init` with your `project_id` and `path` set to `external_project`.
   - Example:
     ```json
     {
       "project_id": "rebel_container",
       "path": "external_project"
     }
     ```
3. **API creates onboarding steps:**
   - The API reads the steps for 'external_project' from onboarding_paths.json.
   - It creates progress records for each step (if not already present).
4. **Query onboarding progress:**
   - Use `GET /onboarding/progress/rebel_container?path=external_project` to see the checklist and status.
5. **Mark steps as completed:**
   - As you complete each step, update the corresponding progress record via the PATCH endpoint.
6. **Promote rules as needed:**
   - Use `POST /rules/{rule_id}/promote` to promote rules to higher scopes (see [Rule Promotion and Hierarchical Scopes](./rule_promotion_and_hierarchical_scopes.md)).

---

## Onboarding Step Details

| Step                          | Description                                                                                  |
|-------------------------------|----------------------------------------------------------------------------------------------|
| register_project              | Register your project in the system for tracking and access control.                         |
| obtain_api_token              | Generate and securely store an API token for authentication.                                 |
| configure_api_url             | Set the correct API base URL for your environment (Docker, cloud, etc.).                     |
| verify_api_connectivity       | Test connectivity and authentication with a simple API call (e.g., `/env`).                  |
| submit_first_rule             | Submit a rule or resource to verify end-to-end API flow.                                     |
| run_onboarding_health_check   | Use a health check endpoint or script to verify environment, tokens, and connectivity.        |
| complete_code_review_objective| Submit code/config for review, or pass an automated code review/linting step.                |
| setup_webhook_endpoint        | Register a webhook endpoint to receive real-time updates or events from the API.              |
| enable_logging_and_monitoring | Configure logging of API requests/responses and set up monitoring for errors or usage.        |
| review_api_rate_limits        | Understand and test API rate limiting, quotas, and error handling for overages.              |
| accept_terms_of_service       | Confirm you have read and accepted the API usage policies.                                   |
| explore_api_docs_and_user_stories | Visit the OpenAPI docs and user story index to discover available endpoints and best practices. |
| setup_automated_testing       | Integrate API calls into your project's CI/CD pipeline or test suite.                        |

---

## 🧠 Saving and Using Memories (Memory Graph API)

External projects can use the memory graph API to store, relate, and search ideas, notes, and code snippets using semantic embeddings and relationships.

### How to use it?
- **Add a memory node:**
  ```bash
  curl -X POST http://localhost:9103/memory/nodes \
    -H "Content-Type: application/json" \
    -d '{"namespace": "notes", "content": "This is an idea about AI memory.", "meta": "{\"tags\":[\"ai\",\"memory\"]}"}'
  ```
- **List all memory nodes:**
  ```bash
  curl http://localhost:9103/memory/nodes | jq .
  ```
- **Add a relationship (edge):**
  ```bash
  curl -X POST http://localhost:9103/memory/edges \
    -H "Content-Type: application/json" \
    -d '{"from_id": "UUID-OF-NODE-1", "to_id": "UUID-OF-NODE-2", "relation_type": "inspired_by", "meta": "{\"note\": \"A inspired B\"}"}'
  ```
- **List all edges:**
  ```bash
  curl http://localhost:9103/memory/edges | jq .
  ```
- **Search for similar nodes:**
  ```bash
  curl -X POST http://localhost:9103/memory/nodes/search \
    -H "Content-Type: application/json" \
    -d '{"text": "Find similar ideas about AI memory.", "namespace": "notes", "limit": 5}'
  ```

For more advanced usage, traversal, and best practices, see [`docs/user_stories/ai_memory_graph_api.md`](docs/user_stories/ai_memory_graph_api.md).

---

## Expected Outcomes
- The project has a visible, trackable onboarding checklist.
- All team members and automation can see and update onboarding status.
- Onboarding is standardized and repeatable for all external projects.

---

## Best Practices
- Always use the onboarding_paths.json template for consistency.
- Automate onboarding initialization in your project setup scripts.
- Regularly query and update onboarding progress to keep status current.
- Review and use the `/onboarding-docs` endpoint for automation and Makefile best practices.
- Use the `/rules/{rule_id}/promote` endpoint to manage rule scopes as your project grows.

---

## References
- Endpoint: `POST /onboarding/init`
- Step template: `onboarding_paths.json`
- Progress: `GET /onboarding/progress/{project_id}?path=external_project`
- Automation docs: `GET /onboarding-docs`
- Rule promotion: `POST /rules/{rule_id}/promote` 
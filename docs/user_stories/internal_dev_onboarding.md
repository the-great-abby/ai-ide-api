# User Story: Internal Developer Onboarding via API

## Motivation
As a core team member or internal developer, I want a standardized onboarding checklist for local development, so I can quickly set up my environment and follow best practices.

---

## Actors
- Internal developer
- Onboarding buddy
- Automation scripts

---

## Preconditions
- The API is running and accessible
- onboarding_paths.json defines the steps for 'internal_dev'

---

## Step-by-Step Actions
1. **Review onboarding and automation docs:**
   - Download and review the onboarding and automation best practices documentation:
     - `GET /onboarding-docs` (automation and Makefile best practices)
     - `GET /onboarding/user_story/internal_dev` (this user story)
2. **Initialize onboarding:**
   - Send a POST request to `/onboarding/init` with your `project_id` and `path` set to `internal_dev`.
   - Example:
     ```json
     {
       "project_id": "my_dev_env",
       "path": "internal_dev"
     }
     ```
3. **API creates onboarding steps:**
   - The API loads the 'internal_dev' steps from onboarding_paths.json and creates progress records.
4. **Check onboarding status:**
   - Use `GET /onboarding/progress/my_dev_env?path=internal_dev` to view your checklist.
5. **Complete steps:**
   - As you finish each setup task, mark it complete via the PATCH endpoint.
6. **Promote rules as needed:**
   - Use `POST /rules/{rule_id}/promote` to promote rules to higher scopes (see [Rule Promotion and Hierarchical Scopes](./rule_promotion_and_hierarchical_scopes.md)).

---

## Onboarding Step Details

| Step                          | Description                                                                                  |
|-------------------------------|----------------------------------------------------------------------------------------------|
| read_onboarding_guide         | Review ONBOARDING.md and internal onboarding user stories to understand the process.          |
| clone_repo                    | Clone the repository to your local machine.                                                   |
| install_dependencies          | Install all required dependencies (Python, Docker, Make, etc.).                              |
| setup_env                     | Set up environment variables and configuration files.                                         |
| run_linting                   | Run linting tools (e.g., `make ai-lint-rules`) to ensure code quality.                       |
| run_tests                     | Run the test suite to verify your setup.                                                      |
| review_coding_standards       | Read through coding standards, rule files, and best practices.                                |
| explore_api_docs_and_user_stories | Visit the OpenAPI docs and user story index to discover available endpoints and workflows. |
| review_ci_cd_pipeline         | Review CI/CD configuration to understand build, test, and deploy processes.                   |
| request_service_access        | Ensure you have access to all required services (DB, cloud, secrets, etc.).                   |
| start_services                | Start all required services (API, DB, etc.).                                                  |
| submit_first_rule             | Propose or submit your first rule to the system.                                              |
| make_first_contribution       | Make your first PR (rule, bugfix, or doc improvement).                                        |
| review_changelog              | Read the latest changelog and recent PRs to get up to speed.                                  |

---

## 🧠 Saving and Using Memories (Memory Graph API)

Internal developers can use the memory graph API to store, relate, and search ideas, notes, and code snippets using semantic embeddings and relationships.

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
- Developers have a clear, actionable onboarding checklist.
- Onboarding is consistent across all team members.
- Progress is visible and can be automated or audited.

---

## Best Practices
- Use onboarding_paths.json as the source of truth for steps.
- Automate onboarding in setup scripts or Makefile targets.
- Keep progress up to date for better support and troubleshooting.
- Review and use the `/onboarding-docs` endpoint for automation and Makefile best practices.
- Use the `/rules/{rule_id}/promote` endpoint to manage rule scopes as your project grows.

---

## References
- Endpoint: `POST /onboarding/init`
- Step template: `onboarding_paths.json`
- Progress: `GET /onboarding/progress/{project_id}?path=internal_dev`
- Automation docs: `GET /onboarding-docs`
- Rule promotion: `POST /rules/{rule_id}/promote` 
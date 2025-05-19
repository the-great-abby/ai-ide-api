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
1. **Call the onboarding initialization endpoint:**
   - Send a POST request to `/onboarding/init` with your `project_id` and `path` set to `external_project`.
   - Example:
     ```json
     {
       "project_id": "rebel_container",
       "path": "external_project"
     }
     ```
2. **API creates onboarding steps:**
   - The API reads the steps for 'external_project' from onboarding_paths.json.
   - It creates progress records for each step (if not already present).
3. **Query onboarding progress:**
   - Use `GET /onboarding/progress/rebel_container?path=external_project` to see the checklist and status.
4. **Mark steps as completed:**
   - As you complete each step, update the corresponding progress record via the PATCH endpoint.

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

## Expected Outcomes
- The project has a visible, trackable onboarding checklist.
- All team members and automation can see and update onboarding status.
- Onboarding is standardized and repeatable for all external projects.

---

## Best Practices
- Always use the onboarding_paths.json template for consistency.
- Automate onboarding initialization in your project setup scripts.
- Regularly query and update onboarding progress to keep status current.

---

## References
- Endpoint: `POST /onboarding/init`
- Step template: `onboarding_paths.json`
- Progress: `GET /onboarding/progress/{project_id}?path=external_project` 
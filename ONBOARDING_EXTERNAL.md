# External/Partner Onboarding

Welcome, external collaborator or partner! This guide will help you get started quickly and use the project's essential features via the public API.

## 1. Quick Start (API-First)
- Register your project and initialize onboarding steps:
  - Send a POST request to `/onboarding/init` with your `project_name` and `path` set to `external_project`.
    ```json
    {
      "project_name": "your_project_name",
      "path": "external_project"
    }
    ```
- Use any HTTP client (curl, httpie, Postman, etc.) to interact with the API.

## 2. Track Onboarding Progress
- List your onboarding checklist and status:
  - `GET /onboarding/progress/{project_name}?path=external_project`
- Mark steps as completed:
  - `PATCH /onboarding/progress/{progress_id}` with `{ "completed": true }`

## 3. Essential API Endpoints
- [POST] `/onboarding/init` — Initialize onboarding steps for your project
- [GET] `/onboarding/progress/{project_name}?path=external_project` — List your onboarding steps and status
- [PATCH] `/onboarding/progress/{progress_id}` — Mark a step as completed or add details
- [GET] `/onboarding/progress` — (Optional) List all onboarding progress (admin only)

## 4. Onboarding Checklist & Step Details
- For a full description of each onboarding step, see:
  - [External Project Onboarding User Story](docs/user_stories/external_project_onboarding.md)
- This user story includes a table describing each step and what is required.

## 5. Getting Help
- If you have questions or need support, reach out via the project's issue tracker or contact your integration lead.

---

**See also:** [Universal Onboarding](ONBOARDING.md) | [Internal Onboarding](ONBOARDING_INTERNAL.md)

## External Project Memory API Onboarding

If you want to use the AI IDE API as a hosted memory (vector) server for your own project (with no Docker or DB access required), follow this onboarding path:

- [External Project Memory API Onboarding →](docs/external/memory_api_onboarding.md)

This guide covers:
- How to get an API key
- How to create a namespace
- How to store and search memory via the API
- Example scripts and troubleshooting

For most external integrations, this is the recommended starting point. 
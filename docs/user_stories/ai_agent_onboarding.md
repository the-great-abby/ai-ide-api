# User Story: AI Agent Onboarding via API

## Motivation
As an AI agent or automated client, I want to initialize and track my onboarding process programmatically, so I can ensure all integration steps are completed and visible to maintainers.

---

## Actors
- AI agent
- Automation scripts
- System integrators

---

## Preconditions
- The API is running and accessible
- onboarding_paths.json defines the steps for 'ai_agent'

---

## Step-by-Step Actions
1. **Initialize onboarding:**
   - Send a POST request to `/onboarding/init` with your `project_id` and `path` set to `ai_agent`.
   - Example:
     ```json
     {
       "project_id": "ai_ide_x",
       "path": "ai_agent"
     }
     ```
2. **API creates onboarding steps:**
   - The API loads the 'ai_agent' steps from onboarding_paths.json and creates progress records.
3. **Check onboarding status:**
   - Use `GET /onboarding/progress/ai_ide_x?path=ai_agent` to view the checklist.
4. **Complete steps:**
   - As the agent completes each integration task, mark it complete via the PATCH endpoint.

---

## Expected Outcomes
- AI agents have a clear, programmatically accessible onboarding checklist.
- Integration is standardized and auditable.
- Progress can be monitored and troubleshooted by maintainers.

---

## Best Practices
- Use onboarding_paths.json as the canonical source for steps.
- Automate onboarding initialization in agent startup scripts.
- Keep progress up to date for transparency and support.

---

## References
- Endpoint: `POST /onboarding/init`
- Step template: `onboarding_paths.json`
- Progress: `GET /onboarding/progress/{project_id}?path=ai_agent` 
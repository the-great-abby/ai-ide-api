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
1. **Initialize onboarding:**
   - Send a POST request to `/onboarding/init` with your `project_id` and `path` set to `internal_dev`.
   - Example:
     ```json
     {
       "project_id": "my_dev_env",
       "path": "internal_dev"
     }
     ```
2. **API creates onboarding steps:**
   - The API loads the 'internal_dev' steps from onboarding_paths.json and creates progress records.
3. **Check onboarding status:**
   - Use `GET /onboarding/progress/my_dev_env?path=internal_dev` to view your checklist.
4. **Complete steps:**
   - As you finish each setup task, mark it complete via the PATCH endpoint.

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

---

## References
- Endpoint: `POST /onboarding/init`
- Step template: `onboarding_paths.json`
- Progress: `GET /onboarding/progress/{project_id}?path=internal_dev` 
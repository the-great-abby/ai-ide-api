# User Story: Submitting a Bug Report with User Story Context

## Motivation
To improve bug triage, context, and resolution, users can now submit a bug report with an optional `user_story` field. This allows reporters to link the bug to a specific workflow, feature, or user scenario, making it easier for developers and AI assistants to understand the impact and reproduce the issue.

## Actors
- End users
- QA testers
- Developers
- AI assistants

## Preconditions
- The API server is running and accessible
- The bug report endpoint (`/bug-report`) is available

## Step-by-Step Actions
1. User encounters a bug in the system.
2. User prepares a bug report including:
    - `description`: What went wrong
    - `reporter`: (Optional) Who is reporting
    - `page`: (Optional) Where the bug occurred
    - `user_story`: (Optional) The user story, workflow, or scenario related to the bug
    - `timestamp`: (Optional) When the bug was observed
3. User submits the bug report via the API:
    ```json
    POST /bug-report
    {
      "description": "Unable to save rule proposal.",
      "reporter": "abby",
      "page": "rule_proposal_page",
      "user_story": "As a user, I want to propose a new rule so that I can improve code quality.",
      "timestamp": "2024-05-12T14:30:00Z"
    }
    ```
4. The API stores the bug report, including the user story context, in the database.
5. Developers and AI assistants can review bug reports and see the associated user story for better context.
6. If any error occurs in the system (not just during bug report submission), the next step is to:
    - Look up the error details using the Reference ID (e.g., via the /admin/errors/{error_id} endpoint)
    - Review related logs for additional context
    - Examine the relevant code to diagnose and resolve the issue

## Expected Outcomes
- Bug reports are more actionable and easier to triage.
- Developers can quickly understand the workflow or feature affected.
- AI assistants can use the user story context to suggest relevant fixes or documentation.

## Best Practices
- Always include a user story or workflow context if possible.
- Reference the user story in related pull requests or documentation.
- Use clear, concise language for both the bug description and user story.

## Example
> **Bug Description:** "The 'Save' button does nothing on the rule proposal page."
>
> **User Story:** "As a user, I want to propose a new rule so that I can improve code quality."

---

**See also:**
- [api_token_onboarding.md](api_token_onboarding.md)
- [ai_memory_graph_api.md](ai_memory_graph_api.md) 
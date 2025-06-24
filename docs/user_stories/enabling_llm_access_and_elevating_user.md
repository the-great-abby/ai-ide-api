---
title: Enabling LLM Access and Elevating User API Token
summary: How to enable LLM access for a project and elevate a user's API token to admin using Makefile targets.
---

## Motivation
To streamline project setup and ensure users have the correct permissions for LLM-powered features, admins must be able to enable LLM access for a project and elevate user tokens to admin level efficiently.

## Actors
- Project Admin
- Regular User

## Preconditions
- Admin token available (in `.api_admin_token` or `.admin_token`)
- Project name or ID known (in `.projectname` or as argument)
- User email known (for elevation)

## Steps: Enabling LLM Access
1. Ensure `.api_admin_token` and `.projectname` are set, or pass as arguments.
2. Run:
   ```bash
   make -f Makefile.ai-llm enable-llm-access
   # or specify:
   make -f Makefile.ai-llm enable-llm-access PROJECT_ID=<project_id> ADMIN_TOKEN=<admin_token>
   ```
3. The Makefile target will print clear feedback on success or failure.

## Steps: Elevating a User's API Token
1. Ensure `.api_admin_token` is set, or pass as `ADMIN_TOKEN`.
2. Run:
   ```bash
   make -f Makefile.ai-admin admin-external-elevate-user PROJECT_ID_OR_NAME=<project_id_or_name> USER_EMAIL=<user_email>
   ```
3. The target will generate an admin token for the user and print the result.

## Expected Outcomes
- LLM access is enabled for the project.
- The specified user receives an admin token for the project.
- Clear feedback is provided for each action.

## Best Practices
- Store admin tokens securely and do not share them unnecessarily.
- Use file-based defaults for convenience, but always verify the correct project and user are targeted.
- Document the process in onboarding guides for new admins.

## Mermaid Diagram

```
flowchart TD
    A[Admin: Has admin token] --> B[Enable LLM Access via Makefile]
    B --> C{LLM Access enabled?}
    C -- Yes --> D[Success message]
    C -- No --> E[Error message]
    A --> F[Elevate User via Makefile]
    F --> G{Admin token, project, user email provided?}
    G -- Yes --> H[Generate admin token for user]
    H --> I[Success message]
    G -- No --> J[Error message]
``` 
# User Story: User Story Completeness Checker

## Motivation
To ensure that every new workflow, Makefile target, or API endpoint is properly documented, the system should automatically check for the presence and completeness of user stories. This supports onboarding, maintenance, and discoverability.

## Actors
- Automation system (runs the completeness checker)
- Developers (review and address missing or incomplete stories)

## Preconditions
- Access to the codebase and `docs/user_stories/` directory.
- Defined conventions for naming and structuring user stories.

## Step-by-Step Actions
1. The worker scans for new or changed Makefile targets, scripts, and API endpoints.
2. It checks for a corresponding user story in `docs/user_stories/`.
3. The worker reports any missing or incomplete user stories, and optionally suggests templates.
4. Developers review the report and add or update user stories as needed.

## Expected Outcomes
- All workflows, targets, and endpoints are documented with clear user stories.
- Onboarding and documentation remain up to date and comprehensive.

## Best Practices
- Suggest templates for missing stories to streamline documentation.
- Integrate checks into CI/CD or code review processes.
- Log all findings and provide actionable feedback to developers.
- Schedule regular scans and allow for manual triggering. 
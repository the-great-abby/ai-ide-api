---
name: "<User Story Name>"
type: "user_story"
summary: "<Short summary of the user story>"
tags: [internal, onboarding, automation]  # e.g., [internal], [external], [onboarding], [api], etc.
visibility: internal  # or external
onboarding_paths: [external_project, internal_dev]  # List of onboarding paths where this story is referenced
related_files:
  - docs/user_stories/<filename>.md
  - scripts/<script_name>.py
  - Makefile
endpoints:
  - /onboarding/init
  - /onboarding/progress/{project_id}
created_by: <author>
created_at: <YYYY-MM-DD>
updated_at: <YYYY-MM-DD>
reviewed: false
review_notes: ""
---

# <User Story Title>

## Motivation
<Describe the motivation for this user story.>

## Actors
- <Actor 1>
- <Actor 2>

## Preconditions
- <Precondition 1>
- <Precondition 2>

## Step-by-Step Actions
1. <Step 1>
2. <Step 2>

## Expected Outcomes
- <Outcome 1>
- <Outcome 2>

## Best Practices
- <Best practice 1>
- <Best practice 2>

## Workflow Diagram

```mermaid
flowchart TD
    A["Start"] --> B["Step 1"]
    B --> C["Step 2"]
    C --> D["Finish"]
```

## References
- <Reference 1>
- <Reference 2> 
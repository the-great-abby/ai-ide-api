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

<Full markdown content of the user story goes here.> 
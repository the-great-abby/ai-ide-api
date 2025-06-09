# User Stories & Documentation Workflow Guide

This guide explains how user stories and documentation are created, organized, and kept up to date in this project. It's designed to help new contributors understand the "why" behind features and how to keep docs useful for everyone.

---

## 1. Overview
- **Purpose:** Ensure every new workflow, automation, or major feature is documented with a user story, and that onboarding/docs stay in sync with the codebase.
- **Scope:** Covers user story creation, documentation best practices, and how to contribute updates.

---

## 2. What is a User Story?
- A user story describes a feature or workflow from the perspective of an end user.
- It includes: motivation, actors, preconditions, step-by-step actions, expected outcomes, and best practices.

---

## 3. Why Are User Stories Important?
- **Discoverability:** New features are easier to find and understand.
- **Onboarding:** New team members can quickly learn how and why things work.
- **Maintenance:** Docs stay up to date as the system evolves.
- **Collaboration:** Everyone can contribute to and improve documentation.

---

## 4. Where Are User Stories and Docs Stored?
- **User stories:**  `docs/user_stories/` (one file per story, e.g., `batch_rule_suggestion.md`)
- **Onboarding & workflow docs:**  `docs/onboarding/`
- **Other docs:**  `docs/` (general), `docs/rules/` (rule-specific), etc.

---

## 5. How to Create or Update a User Story

### A. When to Create a User Story
- When adding a new Makefile target, script, or API endpoint.
- When introducing a new workflow or automation.

### B. User Story Template
```markdown
# [Feature/Workflow Name] User Story

## Motivation
Why does this feature/workflow exist?

## Actors
Who uses it? (e.g., developer, admin, end user, AI agent)

## Preconditions
What needs to be set up or true before starting?

## Steps
1. Step one
2. Step two
3. ...

## Expected Outcomes
What should happen at the end?

## Best Practices
Tips, gotchas, or recommended patterns.
```

### C. Example
See `docs/user_stories/batch_rule_suggestion.md` for a real example.

---

## 6. How to Contribute to Documentation
- **Find the right doc:**  Look in `docs/onboarding/`, `docs/user_stories/`, or the relevant subfolder.
- **Edit or add a file:**  Use Markdown (`.md`). Follow the template for user stories.
- **Submit a PR:**  Propose your changes for review. Reference the user story in code reviews and onboarding docs as needed.

---

## 7. Best Practices
- Keep docs concise and actionable.
- Update docs when workflows or features change.
- Reference user stories in code reviews and onboarding.
- Use clear headings and consistent formatting.
- Encourage everyone to contribute improvements.

---

## 8. Common Pitfalls & Troubleshooting
| Symptom                        | Likely Cause                                  | Solution                                      |
|--------------------------------|-----------------------------------------------|-----------------------------------------------|
| "Feature not documented"       | No user story created                         | Add a user story in `docs/user_stories/`      |
| "Docs out of date"             | Feature changed, docs not updated             | Update docs as part of the PR                 |
| "Hard to find info"            | Docs not organized or linked                  | Add links from onboarding and codebase tour   |
| "Unclear steps or outcomes"    | User story missing details                    | Use the template, add examples                |

---

## 9. Further Reading
- See the [Codebase Tour](CODEBASE_TOUR.md) for links to all major docs.
- Browse `docs/user_stories/` for real examples.

---

*See something missing? Please add your tips or examples!* 
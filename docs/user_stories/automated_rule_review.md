# User Story: Automated Rule Proposal Review

> **Note:** For more specific workflow user stories, see the `docs/user_stories/` directory referenced in project documentation and onboarding materials.

---

## As a developer or AI agent
I want all new rule proposals to be automatically reviewed for validity, completeness, and adherence to project standards
So that the review process is fast, consistent, and reduces manual effort

---

## Acceptance Criteria
- When a new rule proposal is submitted (by human or AI), an automated process:
  - Validates the rule's JSON structure and required fields.
  - Checks for MDC compliance in the `diff` field.
  - Optionally, applies rule-based or LLM-based feedback for common issues (e.g., duplicates, typos, security).
  - Logs the review outcome and any feedback.
  - Notifies the team (via Slack/email/etc.) if human intervention is needed.
- The process is reproducible via a Makefile target and runs in a Dockerized environment.
- All review actions are logged for auditability.
- The workflow is documented in onboarding materials.

---

## Example Workflow
1. **Submission:** A new rule proposal is submitted via API or file drop.
2. **Validation:** The automated review script lints and validates the rule.
3. **Feedback:** If the rule passes, it is marked as valid. If not, feedback is auto-generated and attached.
4. **Notification:** If human review is required, a notification is sent.
5. **Logging:** All actions and feedback are logged for future reference.

---

## References
- See `ONBOARDING.md` for a high-level overview and links to user stories in this directory.
- See Makefile targets: `ai-lint-rule-files`, `ai-fix-rule-files`, and `ai-auto-feedback` for automation details. 
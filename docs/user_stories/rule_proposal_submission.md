# User Story: Submitting a Rule Proposal

## Motivation
To ensure the system's rules remain current, effective, and collaborative, users must be able to propose new rules or suggest changes to existing ones. This process enables continuous improvement and shared governance across the organization.

## Actors
- Contributor (any user with permission to propose rules)
- Reviewer (admin, team lead, or AI agent)
- API Client (automation or integration)

## Preconditions
- The user has access to the system and permission to submit proposals.
- The user has identified a need for a new rule or an update to an existing rule.

## Step-by-Step Actions
1. **Prepare the Proposal:**
   - Gather the required information: rule type, description, diff (markdown), reason for change, references, and submitter info.
   - Optionally include categories, tags, examples, applies_to, and user_story fields for clarity.
2. **Submit the Proposal:**
   - Use the API endpoint `POST /propose-rule-change` or the UI form to submit the proposal.
   - Ensure all required fields are filled. The system will validate the payload and return errors for missing or invalid fields.
3. **Review and Feedback:**
   - The proposal enters the review queue. Reviewers (admins, team leads, or AI agents) may provide feedback, request revisions, or ask questions.
   - The submitter can revise the proposal in response to feedback.
4. **Approval or Rejection:**
   - Once the proposal meets requirements, a reviewer approves or rejects it using the appropriate API endpoint.
   - Approved proposals become active rules and are versioned for future reference.
5. **Versioning and History:**
   - The system records the proposal and its approval in the rule version history for traceability.

## Expected Outcomes
- The proposal is either approved (becoming an active rule) or rejected with clear feedback.
- All actions are auditable and versioned for future reference.
- The process encourages collaboration and continuous improvement.

## Best Practices
- Provide clear, actionable descriptions and diffs.
- Reference related rules or proposals for context.
- Respond promptly to reviewer feedback.
- Use the version history to track changes and rationale.

## Further Reading
- [Rule Proposal Workflow Guide](../onboarding/RULE_PROPOSAL_WORKFLOW.md)
- [API Documentation](../../public_endpoints.py)
- [Feedback Loops Guide](../onboarding/FEEDBACK_LOOPS.md) 
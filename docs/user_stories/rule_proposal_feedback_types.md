# User Story: Providing Feedback on Rule Proposals

## Motivation
To ensure rule proposals are thoroughly reviewed and improved, users must be able to provide structured feedback. Categorizing feedback types helps reviewers and submitters address concerns, answer questions, and implement suggestions efficiently.

## Actors
- Reviewer (admin, team lead, peer, or AI agent)
- Proposal Submitter
- API Client (automation or integration)

## Preconditions
- A rule proposal exists and is available for review.
- The reviewer has permission to submit feedback.

## Step-by-Step Actions
1. **Access the Proposal:**
   - Identify the proposal to review, using the UI or API.
2. **Prepare Feedback:**
   - Choose one of the allowed feedback types:
     - `suggestion`: A recommendation for improvement or clarification.
     - `question`: A request for additional information or clarification.
     - `concern`: An issue or potential problem with the proposal.
   - Write clear, actionable comments to accompany the feedback type.
3. **Submit Feedback:**
   - Use the API endpoint `POST /api/rule_proposals/{proposal_id}/feedback` or the UI form.
   - The system validates the feedback type. If an invalid type is submitted, a 422 error is returned with a list of allowed types.
4. **Review and Response:**
   - The proposal submitter and other reviewers can view feedback, respond, and revise the proposal as needed.

## Expected Outcomes
- Feedback is categorized and actionable, helping to improve the quality of proposals.
- Invalid feedback types are rejected with clear error messages.
- The feedback loop encourages collaboration and continuous improvement.

## Best Practices
- Use the appropriate feedback type for your comment.
- Be specific and constructive in your feedback.
- Reference related rules or proposals when relevant.
- Follow up on feedback to ensure issues are addressed.

## Further Reading
- [Feedback Loops Guide](../onboarding/FEEDBACK_LOOPS.md)
- [Rule Proposal Workflow Guide](../onboarding/RULE_PROPOSAL_WORKFLOW.md)
- [API Documentation](../../public_endpoints.py) 
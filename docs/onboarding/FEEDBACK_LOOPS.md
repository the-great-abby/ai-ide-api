# Feedback Loops Guide

This guide explains the different ways you can provide feedback to the system—whether you're suggesting improvements, reporting bugs, or helping the AI learn. It covers proposals, feedback comments, memory nodes, enhancements, and bug reports.

---

## 1. Overview
- **Purpose:** Make it easy for anyone to provide feedback, suggest improvements, and help the system evolve.
- **Scope:** Covers all feedback channels: proposals, feedback comments, memory, enhancements, and bug reports.

---

## 2. Ways to Provide Feedback

| Feedback Type   | How to Submit                | Where It Goes / How It's Used                |
|----------------|------------------------------|----------------------------------------------|
| **Proposal**   | API (`/propose-rule-change`), UI form | Suggests a new or updated rule; reviewed and may become part of the rule set |
| **Feedback**   | API (`/proposals/{id}/feedback`), UI | Comments or suggestions on a proposal; helps reviewers and submitters improve proposals |
| **Memory Node**| API (`/memory/node`), scripts | Adds knowledge or context to the memory graph; used for AI context and discovery |
| **Enhancement**| API (`/suggest-enhancement`), UI | Suggests an improvement to an existing rule or feature; reviewed and may be accepted/rejected |
| **Bug Report** | API (`/bug-report`), UI       | Reports a bug or issue; triaged and tracked for resolution |

---

## 2a. Allowed Feedback Types for Rule Proposal Feedback

When submitting feedback on a rule proposal (via the API or UI), you must specify a `feedback_type`. Only the following feedback types are accepted:

- `suggestion`
- `question`
- `concern`

Any other value will be rejected with a clear error message. This is enforced at both the API and data validation layers for consistency and safety.

**Why?**
- Ensures feedback is actionable and categorized for reviewers.
- Prevents accidental or inconsistent feedback types from entering the system.

**What happens if you submit an invalid type?**
- The API will return a 422 error with a message listing the allowed types.

**Example:**
```json
{
  "feedback_type": "suggestion",
  "comments": "This rule could be improved by adding more examples."
}
```

---

## 3. How Feedback Is Processed
- **Proposals:** Reviewed by admins, AI, or peers; may receive feedback, be revised, accepted, or rejected.
- **Feedback Comments:** Used to clarify, improve, or challenge proposals; can lead to revisions or new proposals.
- **Memory Nodes:** Enrich the knowledge graph; can be referenced by AI or users for context and recommendations.
- **Enhancements:** Reviewed and prioritized; may become new features or improvements.
- **Bug Reports:** Triaged, tracked, and fixed; status is updated as work progresses.

---

## 4. Best Practices for Actionable Feedback
- Be specific: Describe the issue, suggestion, or context clearly.
- Reference related rules, proposals, or memory nodes if possible.
- Use the appropriate channel (proposal for new rules, bug report for issues, etc.).
- Follow up on feedback—respond to comments, revise proposals, and check status.
- Encourage a culture of constructive, respectful feedback.

---

## 5. Example Feedback Flows
- **Suggesting a new rule:** Submit a proposal → receive feedback → revise → accepted/rejected.
- **Reporting a bug:** Submit a bug report → triaged by team → tracked and fixed.
- **Suggesting an enhancement:** Submit enhancement → reviewed → accepted/rejected.
- **Adding context for AI:** Add a memory node → referenced in future proposals or recommendations.

---

## 6. Further Reading
- [Rule Proposal Workflow Guide](RULE_PROPOSAL_WORKFLOW.md)
- [Memory System Guide](MEMORY_SYSTEM.md)
- [User Stories & Documentation Workflow Guide](USER_STORIES_AND_DOCS.md)

---

*See something missing? Please add your tips or examples!* 
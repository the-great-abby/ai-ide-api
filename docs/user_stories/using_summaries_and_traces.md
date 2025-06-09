# User Story: Using AI Knowledge Summaries and Decision Traces

## Motivation
As a developer or team member, I want to quickly understand the history, context, and key insights about a set of rules or a specific decision, so I can make informed contributions, avoid redundant work, and trust the system's recommendations.

## Actors
- Developer
- Admin
- New contributor
- Auditor

## Preconditions
- The memory system contains rules, proposals, feedback, and other nodes, tagged and linked by topic and relationship.
- Summaries and traces are available in the UI or via API.

---

## Scenario 1: Using AI Knowledge Summaries

### Steps
1. A new contributor joins the project and wants to understand the current state of "pytest" rules.
2. They visit the "pytest" topic page in the UI (or use the API) and see an AI-generated summary at the top.
3. The summary concisely explains recent changes, key proposals, and open questions about pytest rules.
4. The contributor clicks on the summary to see the underlying rules and proposals it's based on.
5. They use this context to propose a new rule or avoid duplicating existing work.

### Expected Outcomes
- The contributor quickly gets up to speed on the topic.
- They make more relevant, high-quality contributions.
- The team spends less time answering onboarding questions.

---

## Scenario 2: Using Explainable Decision Tracing

### Steps
1. An admin reviews a rule that seems controversial or unclear.
2. They click "Show Decision Trace" in the rule detail view.
3. The system displays a visual and/or textual trace showing:
   - The original proposal
   - Feedback and revisions
   - Related rules and superseded versions
   - Who made each change and when
4. The admin follows links to read the original feedback and see why the rule was updated.
5. They use this context to decide whether to accept a new proposal or suggest further changes.

### Expected Outcomes
- The admin understands the full history and rationale behind the rule.
- Decisions are more transparent and auditable.
- The team can resolve disputes or confusion more easily.

---

## Best Practices
- Always check summaries and traces before proposing changes or reviewing rules.
- Use summaries to onboard quickly and identify knowledge gaps.
- Use traces to audit decisions, resolve disputes, and build trust in the system.
- Provide feedback on summaries and traces to help improve their quality.

---

*See something missing? Please add your tips or examples!* 
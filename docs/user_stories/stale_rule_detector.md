# User Story: Stale Rule Detector

## Motivation
To prevent knowledge rot and ensure that rules remain accurate and actionable, the system should automatically detect and flag rules that are outdated, unmaintained, or contradicted by recent code changes.

## Actors
- Automation system (runs the stale rule detector)
- Developers (review and update flagged rules)

## Preconditions
- Rules and knowledge base entries have timestamps or last-modified metadata.
- Access to recent code changes and commit history.

## Step-by-Step Actions
1. The worker scans all rules and knowledge base entries.
2. It identifies entries that:
   - Have not been updated in a configurable period (e.g., 6 months)
   - Are contradicted by recent code changes or new rules
   - Are marked as deprecated but not removed
3. The worker flags these entries and generates a report for developer review.
4. Optionally, the worker can open issues or notify maintainers for follow-up.

## Expected Outcomes
- Outdated or contradicted rules are reviewed, updated, or removed in a timely manner.
- The knowledge base remains current and trustworthy.

## Best Practices
- Integrate with code review or issue tracker for follow-up actions.
- Allow configuration of staleness thresholds and notification methods.
- Log all flagged entries and actions taken.
- Schedule regular scans and allow for manual triggering. 
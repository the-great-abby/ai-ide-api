# Developer Guide

Welcome to the AI-IDE API Developer Guide! This document is your central map for understanding, contributing to, and maintaining this project.

## Quick Links
- [Onboarding](../ONBOARDING.md)
- [Backup & Restore User Story](user_stories/merge_backups_with_smart_script.md)
- [Testing Workflow](user_stories/testing_flow.md)
- [Database Migrations](user_stories/database_migrations.md)
- [Rule Proposal Workflow](user_stories/rule_proposal_workflow.md)
- [User Story Index](user_stories/INDEX.md)

## Common Workflows
- **Run tests:** See [Testing Workflow](user_stories/testing_flow.md)
- **Merge backups:** See [Backup & Restore User Story](user_stories/merge_backups_with_smart_script.md)
- **Propose a new rule:** See [Rule Proposal Workflow](user_stories/rule_proposal_workflow.md)
- **Restore a database:** See [Backup & Restore User Story](user_stories/merge_backups_with_smart_script.md)
- **Run database migrations:** See [Database Migrations](user_stories/database_migrations.md)

## Best Practices
- Use Makefile.ai targets for all automation and testing.
- Reference user stories in code reviews and onboarding.
- Keep user stories and documentation up to date with new workflows.
- Use the user story index to discover existing workflows before creating new ones.
- Prefer running merges and migrations in a controlled environment before production.

## Keeping Docs Up to Date
- When adding a new workflow, automation, or major feature, create or update a user story in `docs/user_stories/`.
- Reference user stories in Makefile targets, scripts, and code comments.
- Update the [User Story Index](user_stories/INDEX.md) when adding new stories.

---

For more details, see the referenced user stories and onboarding docs. 
# Collaborative Knowledge Curation User Story & Design Spec

## Motivation
As a contributor or AI agent, I want to propose merges, splits, or edits to memory nodes—like a "pull request" for knowledge—so the memory graph stays clean, up-to-date, and relevant as the system evolves.

## Actors
- Developer
- Admin
- AI agent
- Knowledge curator

## Preconditions
- Memory system supports versioning and relationships between nodes.
- UI or API for proposing and reviewing knowledge edits is available.

## Steps / Workflow
1. User or AI identifies redundant, outdated, or related memory nodes.
2. They propose a merge (combine nodes), split (separate a node into multiple), or edit (update content or metadata).
3. The proposal is reviewed by admins, peers, or AI (with comments and feedback).
4. Once approved, the change is applied: nodes are merged, split, or updated, and version history is recorded.
5. The system links the new/updated nodes to their predecessors for traceability.

## Expected Outcomes
- The memory graph remains organized and relevant.
- Redundant or outdated knowledge is consolidated or removed.
- All changes are auditable and reversible.

## Best Practices
- Propose focused, well-documented changes (one merge/split/edit per proposal).
- Use clear commit messages and link to related nodes.
- Review changes for accuracy and completeness.
- Maintain version history and provenance for all edits.

---

# High-Level Design Doc

## 1. Proposing Merges/Splits/Edits
- UI/API for selecting nodes and proposing a merge, split, or edit.
- Proposal includes rationale, affected nodes, and suggested changes.

## 2. Review Process
- Proposals are reviewed by admins, peers, or AI agents.
- Reviewers can comment, request changes, or approve.
- Approved changes are applied; rejected changes are archived.

## 3. Versioning & Traceability
- All changes are versioned; old versions are archived but accessible.
- New nodes link to predecessors via relationships (e.g., `merged_from`, `split_from`, `edited_from`).

## 4. UI/API
- UI for browsing, proposing, and reviewing knowledge curation proposals.
- API endpoints for submitting and managing proposals.

## 5. Research Opportunities
- Study how collaborative curation impacts knowledge quality and system evolution.
- Experiment with AI-assisted curation and conflict resolution.

---

*See something missing? Please add your tips or examples!* 
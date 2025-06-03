---
title: File Size Limit Rule for Codebase Maintainability
date: 2024-05-23
authors: [ai-ide-team]
---

# User Story: File Size Limit for Codebase Health

## Motivation
Large files can cause issues for update models, slow down development, and make code harder to maintain. To ensure the codebase remains modular, maintainable, and AI-friendly, we enforce a maximum file size rule. When a file approaches this limit, developers should refactor and reorganize code to keep files streamlined and distributed.

## Actors
- Developers
- Code reviewers
- Automated CI tools
- AI code assistants

## Preconditions
- The codebase is actively developed and updated
- Automated tools or code review processes can check file sizes

## Actions
1. **Monitor file sizes** during development and CI runs.
2. **Warn or block** commits that introduce files exceeding the size threshold (e.g., 500 KB for source code, configurable per language/project).
3. **Refactor large files** by splitting them into smaller, focused modules or components.
4. **Document refactoring** in commit messages and PR descriptions.
5. **Review code organization** regularly to prevent file bloat.

## Expected Outcomes
- No single source file exceeds the configured size limit
- Code is more modular and easier to update
- Update models and AI tools perform better on the codebase
- Refactoring becomes a regular, expected part of development

## Best Practices
- Set language-appropriate file size limits (e.g., 500 KB for Python, 1 MB for markdown/docs)
- Use linters or pre-commit hooks to enforce file size rules
- Refactor early—don't wait for files to become unmanageable
- Favor composition and modularity over monolithic files
- Document major refactors for future maintainers

## Rationale
Keeping files small and focused improves maintainability, enables better AI assistance, and reduces the risk of update failures. This rule helps teams proactively manage code complexity and technical debt. 
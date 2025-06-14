# Cursor MDC Rule Format (Version 2)

## Overview
Cursor uses `.mdc` (Markdown C) files to define project rules for AI context. These rules are picked up by the agent when placed in the `.cursor/rules/` directory.

## File Location
- Place all rule files in `.cursor/rules/` at the project root.
- Nested `.cursor/rules/` directories in subfolders are supported for scoped rules.

## File Naming
- Use a three-digit prefix for organization and priority (optional but recommended):
  - `001-Core-Security.mdc`, `100-API-Integration.mdc`, `200-Pattern-Rule.mdc`
- File extension must be `.mdc`.

## YAML Frontmatter (Required)
Each `.mdc` file must start with a YAML frontmatter block:

```yaml
---
description: Short summary of the rule
globs: ["src/**/*.py"] # File patterns (optional)
alwaysApply: false # true to always include, false for conditional
---
```

- `description`: (Required) What the rule does.
- `globs`: (Optional) File patterns that trigger the rule.
- `alwaysApply`: (Optional, default false) Always include this rule in context.

## Rule Content
- Write actionable, concise instructions in Markdown after the frontmatter.
- You may use lists, code blocks, and references to files (e.g., `@filename.ts`).

## Canonical Example
```mdc
---
description: Enforce API validation standards
globs: ["api/**"]
alwaysApply: false
---

- Use zod for all API validation.
- Define return types with zod schemas.
- Export types generated from schemas.
- All endpoints must return a consistent error format.
```

## Best Practices
- Keep rules focused and under 500 lines.
- Split large concepts into multiple rules.
- Use version control for `.cursor/rules/`.
- Reference: [Cursor Docs: Rules](https://docs.cursor.com/context/rules)
- Community: [Forum Best Practices](https://forum.cursor.com/t/my-best-practices-for-mdc-rules-and-troubleshooting/50526)

## References
- [Medium: A Rule That Writes the Rules](https://medium.com/@devlato/a-rule-that-writes-the-rules-exploring-rules-mdc-288dc6cf4092)
- [Cursor Docs: Rules](https://docs.cursor.com/context/rules)
- [Forum: Best Practices for MDC Rules](https://forum.cursor.com/t/my-best-practices-for-mdc-rules-and-troubleshooting/50526) 
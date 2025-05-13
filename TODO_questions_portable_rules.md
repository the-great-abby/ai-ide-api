# TODO: Questions for Making Rules Portable

This document tracks the key questions and tasks to address when designing portable rules for use across multiple projects.

---

## Deferred Task List: Making Rules Portable

1. **Scope & Purpose**
   - Define which project types the rules will apply to (e.g., Python, .NET, Node.js, etc.)
   - Clarify the purpose of each rule set (code style, testing, CI/CD, etc.)

2. **Current Rule Inventory**
   - List existing rules to be made portable
   - Decide which rules to exclude or rewrite

3. **Project Differences**
   - Document main differences between projects (languages, frameworks, deployment, etc.)
   - Identify constraints to abstract in portable rules

4. **Rule Format & Consumption**
   - Choose a storage and sharing format (Markdown, JSON, repo, etc.)
   - Decide how projects will consume the rules (docs, linting, pre-commit, etc.)

5. **Customization & Overrides**
   - Determine if/how projects can override or extend base rules
   - Plan for rule versioning or tagging

6. **Examples & References**
   - Collect examples of good/bad portable rules
   - Identify industry standards or open-source rule sets to align with

---

_You can revisit or update this list as you progress with making your rules portable._ 
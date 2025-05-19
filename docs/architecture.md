# AI-IDE Rule Suggestion & Proposal System

## Overview

This system combines fast static code analysis with LLM-powered (Ollama) suggestions to continuously improve code quality and developer experience. It automatically detects code patterns, proposes new rules, and helps maintain a living set of best practices.

## Recent Enhancements

### Rule Proposal Feedback Loop

- **Endpoints:**
  - `POST /api/rule_proposals/{proposal_id}/feedback` — Submit anonymous feedback (accept, reject, needs_changes, comments).
  - `GET /api/rule_proposals/{proposal_id}/feedback` — List all feedback for a proposal.
- **Purpose:** Enables users to provide feedback on rule proposals, supporting continuous improvement and community-driven rule curation.

### Database Model

- **Table:** `rule_proposal_feedback`
  - Fields: `id`, `rule_proposal_id`, `feedback_type`, `comments`, `created_at`
- **Migration:** Managed via Alembic, auto-discovered by importing the model in `migrations/env.py`.

### Makefile Enhancements

- **`api-up` target:** Starts both API and database containers.
- **Pre-commit Docker integration:** Run code quality checks in a containerized environment.

### Testing & Data Management

- **Backup:** `make -f Makefile.ai ai-db-backup`
- **Restore:** `make -f Makefile.ai ai-db-restore-data BACKUP=backups/yourfile.sql`
- **Schema reset:** `make -f Makefile.ai ai-db-nuke` and `make -f Makefile.ai ai-db-migrate`

---

For more details, see the relevant sections in this documentation.

---

## Architecture Diagram

```
+-------------------+      +-------------------+      +-------------------+
|                   |      |                   |      |                   |
|  Source Codebase  +----->+  Static Checkers  +----->+  Rule Suggestions |
|                   |      |  (Python/AST/RE)  |      |   (JSON Output)   |
+-------------------+      +-------------------+      +-------------------+
                                                           |
                                                           v
                                                +-----------------------+
                                                |   LLM (Ollama)        |
                                                | (optional, for        |
                                                |  richer proposals)    |
                                                +-----------------------+
                                                           |
                                                           v
                                                +-----------------------+
                                                | Rule Proposal API     |
                                                | (Flask/FastAPI/etc.)  |
                                                +-----------------------+
                                                           |
                                                           v
                                                +-----------------------+
                                                | Rule Management DB    |
                                                +-----------------------+
```

---

## Workflow

1. **Static Pattern Checkers**
   - Run on the codebase using `scripts/suggest_rules.py`.
   - Detect common issues (e.g., print statements, direct SQL, use of `eval`, bare excepts, etc.).
   - Output a list of rule suggestions as JSON.

2. **LLM-Powered Expansion (Optional)**
   - The static suggestions and/or code snippets are sent to Ollama (LLM).
   - Ollama generates richer rule proposals: explanations, enforcement details, examples, and documentation.
   - This step is handled by scripts like `scripts/ai_rule_proposal_bot.py` or `auto_code_review.py`.

3. **Rule Proposal Submission**
   - Proposals are submitted to the Rule Proposal API.
   - The API stores, reviews, and manages rule proposals in the database.

4. **Developer Feedback Loop**
   - Developers review, accept, or reject rule proposals.
   - Accepted rules are enforced in future code reviews and static checks.

---

## Key Components

- **Static Checkers:**  
  - Fast, deterministic, catch common issues.
  - Examples: `check_print_statements`, `check_eval_usage`, `check_bare_except`, etc.

- **LLM (Ollama):**  
  - Adds context, explanations, and project-specific best practices.
  - Can generate new rules or improve static suggestions.

- **Rule Proposal API:**  
  - Central place to submit, review, and manage rules.

---

## Example Flow

1. Developer runs `python scripts/suggest_rules.py .`
2. Static checkers output:
   ```json
   [
     {"rule_type": "no_eval", "description": "eval() found...", ...},
     {"rule_type": "bare_except", "description": "bare except found...", ...}
   ]
   ```
3. (Optional) Output is sent to Ollama for richer proposals.
4. Proposals are POSTed to `/propose-rule-change` API.
5. Rules are reviewed and, if accepted, enforced in future code and reviews.

---

## Benefits

- **Speed:** Static checkers catch most issues instantly.
- **Depth:** LLM can explain, contextualize, and propose new rules.
- **Automation:** New rules are proposed and managed with minimal manual effort.
- **Continuous Improvement:** The system evolves as the codebase and team practices change. 
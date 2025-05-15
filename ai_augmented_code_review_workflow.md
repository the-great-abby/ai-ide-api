# User Story: End-to-End AI-Augmented Code Review & Rule Proposal Workflow

## Overview
This user story describes how a developer (human or AI) can leverage the Ollama-powered code review and rule proposal system to continuously improve code quality, enforce best practices, and integrate new rules into daily development.

---

## Actors
- **Developer:** Writes and reviews code, proposes and reviews rules.
- **AI Reviewer (Ollama):** Analyzes code, suggests improvements, generates rule proposals.
- **Rule Proposal API:** Central service for submitting, reviewing, and managing rules.
- **Team Lead/Reviewer:** Approves, rejects, or requests changes to rule proposals.

---

## End-to-End Workflow

### 0. LLM Model Setup (Ollama)
- **Download the Ollama model:**
  ```bash
  make -f Makefile.ai ai-ollama-pull-model
  # Or specify a different model:
  make -f Makefile.ai ai-ollama-pull-model OLLAMA_MODEL=llama3:70b-instruct-q5_K_M
  ```
- **Start the Ollama service:**
  ```bash
  make -f Makefile.ai ai-ollama-serve-docker-gateway
  # Or run in the background:
  make -f Makefile.ai ai-ollama-serve-docker-gateway-bg
  ```
- **View Ollama logs:**
  ```bash
  make -f Makefile.ai ai-ollama-logs
  ```

### 1. Code Authoring & Static Analysis
- Developer writes or updates code.
- Run static checkers:
  ```bash
  python scripts/suggest_rules.py .
  ```
- Review the output for common issues and improvement suggestions.

### 2. LLM (Ollama) Expansion (Optional but Recommended)
- Send static checker output and/or code snippets to Ollama for deeper analysis:
  ```bash
  python scripts/ai_rule_proposal_bot.py <suggestions.json>
  # or
  python auto_code_review.py <file_or_directory>
  ```
- Ollama generates richer rule proposals: explanations, enforcement details, examples, and documentation.

### 3. Rule Proposal Submission
- Submit proposals to the Rule Proposal API:
  ```bash
  curl -X POST http://localhost:9103/propose-rule-change -H 'Content-Type: application/json' -d @proposal.json
  ```
- Proposals are stored and tracked in the system.

### 4. Review & Feedback Loop
- Team members and AI review proposals via the API or UI.
- Provide feedback using:
  - `POST /api/rule_proposals/{proposal_id}/feedback` (accept, reject, needs_changes, comments)
- Iterate on proposals based on feedback until consensus is reached.

### 5. Rule Acceptance & Enforcement
- Accepted rules are versioned and stored.
- Static checkers are updated to enforce new rules in future code reviews.
- Changelog endpoints (`/changelog`, `/changelog.json`) keep everyone up to date.

### 6. Continuous Improvement
- Repeat the process as code and best practices evolve.
- Use Makefile.ai for all DB, migration, and test operations to ensure consistency.

---

## Best Practices for Daily Development Integration

- **Automate static and LLM checks** as part of pre-commit hooks or CI pipelines.
- **Encourage feedback** from both humans and AI on all rule proposals.
- **Always use Makefile.ai** for environment, DB, and test management.
- **Document rationale and examples** for every rule/enhancement.
- **Review the changelog** regularly to stay current with enforced rules.
- **Onboard new team members and AIs** using the onboarding docs and this workflow.

---

## Example Daily Workflow

1. Pull latest code and rules.
2. Write or update code.
3. Run static and LLM-powered checks.
4. Submit or review rule proposals as needed.
5. Provide or review feedback.
6. Approve, reject, or iterate on proposals.
7. Ensure all tests pass using Makefile.ai targets.
8. Push changes and repeat!

---

## Goal
By following this workflow, the team (human and AI) can:
- Catch issues early
- Continuously improve coding standards
- Share best practices
- Automate and scale code review
- Keep the rule set living and relevant

> **Note:** The `ollama-functions` container (required for LLM-powered endpoints like `/review-code-files-llm`) does **not** start by default for speed. You must start it manually when you want LLM-assisted code review:
> 
> ```bash
> docker-compose up -d ollama-functions
> # or
> make -f Makefile.ai ai-up-ollama-functions
> ``` 
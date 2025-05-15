# User Story: End-to-End AI-Augmented Code Review Workflow Demo

## Motivation
As a developer or reviewer, I want to run a fully automated, reproducible, and AI-augmented code review workflow using Docker Compose, so that I can ensure all rule files are compliant, receive AI-powered feedback, and propose improvements efficiently.

## Actors
- **Developer/Reviewer:** Initiates the workflow and reviews results.
- **AI Agent (LLM):** Provides automated feedback and suggestions.
- **Docker Compose Services:** Ensure environment consistency and reproducibility.

## Preconditions
- The repository is up to date with the latest code and rules.
- Docker Compose is running with all required services (`api`, `db-test`, `misc-scripts`, etc.).
- The rule file(s) to be reviewed exist (e.g., `.cursor/rules/ai_augmented_code_review_workflow.mdc`).

## Steps (End-to-End Demo)
1. **Lint a Rule File in Docker**
   - Command:
     ```bash
     make -f Makefile.ai ai-lint-rule-docker [RULE_FILE=path/to/file]
     ```
   - *Checks for formatting, frontmatter, and compliance issues using the misc-scripts service.*

2. **Run AI Feedback in Docker**
   - Command:
     ```bash
     make -f Makefile.ai ai-auto-feedback-docker [RULE_FILE=path/to/file]
     ```
   - *Generates AI-powered feedback for the rule file using the misc-scripts service.*

3. **Batch Suggest/Propose Rules (Optional)**
   - Command:
     ```bash
     make -f Makefile.ai ai-batch-suggest-rules-docker
     ```
   - *Runs batch suggestion/proposal workflow for rules using the misc-scripts service.*

4. **Review Results**
   - Check terminal output for linting errors, warnings, and AI feedback.
   - Review proposals and feedback in the admin frontend or via API endpoints.

5. **(Optional) Run Tests**
   - Command:
     ```bash
     make -f Makefile.ai ai-test PYTEST_ARGS="-x"
     ```
   - *Ensures all changes are safe and compliant.*

## Expected Outcomes
- All rule files are checked for compliance and best practices.
- AI-generated feedback and suggestions are available for review.
- New rule proposals can be created automatically.
- The workflow is fully reproducible and runs in Docker Compose for consistency.

## Best Practices
- Always use the Dockerized Makefile targets for linting and feedback.
- Keep rule files and scripts up to date.
- Review AI feedback and proposals in the UI or via API endpoints.
- Run tests after making changes to ensure stability.

## References
- Makefile.ai targets: `ai-lint-rule-docker`, `ai-auto-feedback-docker`, `ai-batch-suggest-rules-docker`
- Scripts: `misc_scripts/lint_rule.py`, `misc_scripts/auto_feedback.py`, `misc_scripts/batch_suggest_rules.py`
- Rule file example: `.cursor/rules/ai_augmented_code_review_workflow.mdc` 
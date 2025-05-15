# User Story: Full AI-Augmented Code Review & Rule Management Workflow

## Motivation
As a developer, reviewer, or rule maintainer, I want to leverage automated linting, AI-powered feedback, batch rule suggestion, and human-in-the-loop review to ensure high-quality, consistent, and continuously improving rules and code standards across the project.

## Actors
- **Developer/Reviewer:** Initiates and reviews rule changes, proposals, and feedback.
- **AI Agent (LLM):** Provides automated feedback, suggestions, and batch rule proposals.
- **Admin/Approver:** Reviews, accepts, or rejects proposals and feedback.
- **Docker Compose Services:** Ensure reproducibility and environment consistency.

## Preconditions
- The repository is up to date with the latest code, rules, and models.
- Docker Compose is running with all required services (`api`, `db-test`, `misc-scripts`, etc.).
- The Ollama LLM service is running and accessible to containers.

## Steps (Full End-to-End Workflow)

1. **Lint Rule Files**
   - Ensure all `.mdc` rule files have valid YAML frontmatter and required fields.
   - Command:
     ```bash
     make -f Makefile.ai ai-lint-mdc-docker
     ```

2. **Run AI Feedback on Proposals**
   - Use the LLM to generate and submit feedback for pending rule proposals.
   - Command:
     ```bash
     make -f Makefile.ai ai-auto-feedback-docker RULE_FILE=/app/.cursor/rules/yourfile.mdc
     ```

3. **Batch Suggest/Propose Rules (Optional)**
   - Use the LLM to suggest and propose new rules in batch.
   - Command:
     ```bash
     make -f Makefile.ai ai-batch-suggest-rules-docker
     ```

4. **Review Results**
   - Check terminal output for feedback and suggestions.
   - Review proposals and feedback in the admin frontend or via API endpoints.

5. **Manual Review & Approval**
   - Use the admin UI or API to review, accept, or reject proposals and feedback.
   - Commands:
     ```bash
     make -f Makefile.ai ai-list-pending
     make -f Makefile.ai ai-approve-rule PROPOSAL_ID=...
     make -f Makefile.ai ai-reject-rule PROPOSAL_ID=...
     ```

6. **Run Tests**
   - Ensure all changes are safe and compliant.
   - Command:
     ```bash
     make -f Makefile.ai ai-test PYTEST_ARGS="-x"
     ```

7. **Monitor and Iterate**
   - Use logs and reports to monitor the workflow.
   - Update rules, scripts, and models as needed.

## Expected Outcomes
- All rule files are checked for compliance and best practices.
- AI-generated feedback and suggestions are available for review.
- New rule proposals can be created and batch-processed automatically.
- Human reviewers can approve or reject proposals and feedback.
- The workflow is fully reproducible and runs in Docker Compose for consistency.
- All changes are tested for safety and compliance.

## Best Practices
- Always use the Dockerized Makefile targets for linting, feedback, and testing.
- Keep rule files, scripts, and models up to date.
- Review AI feedback and proposals in the UI or via API endpoints.
- Run tests after making changes to ensure stability.
- Monitor logs and iterate on the workflow for continuous improvement.

## References
- Makefile.ai targets: `ai-lint-mdc-docker`, `ai-auto-feedback-docker`, `ai-batch-suggest-rules-docker`, `ai-list-pending`, `ai-approve-rule`, `ai-reject-rule`, `ai-test`
- Scripts: `misc_scripts/lint_mdc.py`, `misc_scripts/auto_feedback.py`, `misc_scripts/batch_suggest_rules.py`
- Rule file example: `.cursor/rules/ai_augmented_code_review_workflow.mdc` 
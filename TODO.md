# Project TODO & Roadmap

This document tracks the prioritized roadmap for improving the project during and after the current refactor/testing phase. Check off items as they are completed!

---

## 1. Testing & CI/CD Foundation (Top Priority)
- [ ] Make all tests pass consistently (locally and in CI)
- [ ] Add/enforce test coverage (target: 80%+; add badge to README)
- [ ] Parallelize tests with pytest-xdist
- [ ] Add pre-commit hooks for linting, formatting, static analysis (black, isort, flake8, mypy)

## 2. Schema & Data Consistency
- [ ] Complete all in-flight migrations (rulesdb and memorydb)
- [ ] Audit and enforce type consistency in all models (SQLAlchemy & Pydantic)
- [ ] Add tests for serialization/deserialization edge cases
- [ ] Centralize configuration using .env files and a config loader (e.g., Pydantic BaseSettings)

## 3. Developer Experience & Automation
- [ ] Create a one-liner onboarding target (e.g., `make quickstart`)
- [ ] Add a Makefile `help` target listing/describing all commands
- [ ] Ensure all scripts and Makefile targets have comments and usage examples
- [ ] Document that 'test-ollama-functions' is required for some tests but not started by default; add a Makefile target and onboarding step to start it as needed

## 4. API & Documentation
- [ ] Ensure all endpoints are documented in OpenAPI/Swagger
- [ ] Standardize and enrich error messages (especially onboarding/token flows)
- [ ] Keep user stories and onboarding docs in sync with new features/workflows

## 5. Security & Best Practices
- [ ] Review token generation, storage, and revocation for best practices
- [ ] Regularly audit and update dependencies for vulnerabilities

## 6. Modularization & Scalability
- [ ] Refactor large modules into subpackages as needed
- [ ] Ensure all public functions/classes have type hints and docstrings

## Junior Onboarding & Experience Improvements
- [ ] Improve and simplify onboarding docs (add screenshots, examples, clarify steps)
- [ ] Add more code comments, especially in tricky or critical sections
- [ ] Create a "How it Works" doc (high-level overview, key files, diagrams)
- [ ] Document common errors and how to fix them
- [ ] Encourage and document a culture of asking questions
- [ ] Add example PRs to show what a good pull request looks like
- [ ] Highlight learning opportunities (Docker, FastAPI, SQLAlchemy, etc.)

## AI Researcher/Developer Experience Improvements
- [ ] Add a "What This Project Does" and "Who Should Use This" section to the README
- [ ] Add a high-level architecture diagram to the docs or README
- [ ] Create a feature/capability table with links to relevant docs/code
- [ ] Add a glossary of key terms (e.g., rule proposal, namespace, memorydb)
- [ ] Create a centralized "Start Here" doc for new contributors
- [ ] Add a dedicated AI/ML section in the docs (models used, how to extend, inference, etc.)
- [ ] Provide Jupyter notebooks or API usage examples for research workflows
- [ ] Add experiment tracking or document how to use tools like MLflow/W&B
- [ ] Tag/label docs by audience (Researchers, Devs, New Users, etc.)
- [ ] Cross-link docs and code comments for easier navigation
- [ ] Keep changelog and roadmap up to date

---

**Suggested Immediate Next Steps:**
1. Finish and apply all migrations (rulesdb and memorydb)
2. Get all tests green
3. Add/enforce coverage and pre-commit
4. Centralize config and add quickstart
5. Standardize error handling and API docs

---

**Note:** Both junior and senior feedback agree: **getting all tests working is the top priority!**

---

**Note:** Revisit these AI/ML and documentation improvements after test isolation and test reliability are complete.

---

*Update this file as you make progress or reprioritize tasks!* 
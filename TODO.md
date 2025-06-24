# Project TODO & Roadmap

This document tracks the **core development priorities** for improving the project during and after the current refactor/testing phase. Check off items as they are completed!

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

**Other TODO Files:**
- `SECURITY_TODO.md` - Security and best practices
- `ONBOARDING_TODO.md` - Junior developer experience improvements  
- `RESEARCH_TODO.md` - AI researcher/developer experience improvements
- `FUTURE_TODO.md` - Modularization, scalability, and future enhancements

---

*Update this file as you make progress or reprioritize tasks!* 
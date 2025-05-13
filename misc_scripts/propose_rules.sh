#!/bin/bash
for rulefile in ai_ide_rules/*.json; do
  echo "Proposing: $rulefile"
  make -f Makefile.ai ai-propose-rule RULE_FILE="$rulefile"
done
echo "All AI-IDE rule proposals submitted."

# 1. Automation via Makefile.ai
echo "Proposing: Automation via Makefile.ai"
make -f Makefile.ai ai-propose-rule \
  RULE_TYPE=workflow \
  DESCRIPTION='All automation (tests, migrations, builds, etc.) must be run via Makefile.ai targets, not by running commands directly.' \
  DIFF='---\ndescription: All automation (tests, migrations, builds, etc.) must be run via Makefile.ai targets, not by running commands directly.\nglobs: "**/*"\n---\n# Makefile.ai Required for Automation\n\n**Rule:**  \nAll test, migration, build, and environment setup commands must be executed using `Makefile.ai` targets. Do **not** run scripts or commands directly (e.g., `pytest`, `alembic`, `docker compose`, etc.).\n\n**Rationale:**  \n- Ensures consistent, reproducible automation for both humans and AI agents.\n- Centralizes workflow changes in one place (`Makefile.ai`).\n- Prevents environment drift and hard-to-debug issues.\n- Aligns with project onboarding and integration best practices.\n\n**How to comply:**  \n- Use `make -f Makefile.ai <target>` for all automation tasks.\n- See [ONBOARDING.md](../ONBOARDING.md) for a full list of targets and usage examples.\n\n**Examples:**\n```sh\nmake -f Makefile.ai ai-test\nmake -f Makefile.ai ai-db-migrate\nmake -f Makefile.ai ai-up\n```' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"workflow","automation"' \
  TAGS='"makefile","portable"' \
  PROJECT=shared-rules \
  APPLIES_TO='"all"' \
  APPLIES_TO_RATIONALE='This rule applies to all projects using Makefile.ai for automation.' \
  EXAMPLES='make -f Makefile.ai ai-test'

echo

# 2. Test Isolation
echo "Proposing: Test Isolation"
make -f Makefile.ai ai-propose-rule \
  RULE_TYPE=testing \
  DESCRIPTION='Tests must be isolated and not depend on external state.' \
  DIFF='---\ndescription: Tests must be isolated and not depend on external state.\nglobs: "tests/**/*"\n---\n# Test Isolation\n\n**Rule:**  \nAll tests must be written so that they do not depend on external state or the results of other tests.\n\n**Rationale:**  \n- Ensures tests are reliable and can be run in any environment.\n- Prevents flaky or non-deterministic test results.\n\n**Examples:**\n```python\ndef test_example(tmp_path):\n    # Use tmp_path for file operations to avoid global state\n    ...\n```' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"testing","quality"' \
  TAGS='"pytest","portable"' \
  PROJECT=shared-rules \
  APPLIES_TO='"python","pytest","ci"' \
  APPLIES_TO_RATIONALE='Applies to all Python projects using pytest or similar frameworks.' \
  EXAMPLES='def test_example(tmp_path): ...'

echo

# 3. Linting and Formatting
echo "Proposing: Linting and Formatting"
make -f Makefile.ai ai-propose-rule \
  RULE_TYPE=code_style \
  DESCRIPTION='All code must pass linting and formatting checks before merge.' \
  DIFF='---\ndescription: All code must pass linting and formatting checks before merge.\nglobs: "**/*"\n---\n# Linting and Formatting Required\n\n**Rule:**  \nAll code must pass linting and formatting checks before it can be merged into the main branch.\n\n**Rationale:**  \n- Maintains code quality and consistency.\n- Reduces code review friction.\n\n**Examples:**\n- Run `black .` for Python formatting.\n- Run `eslint .` for JavaScript/TypeScript.' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"code_style","quality"' \
  TAGS='"lint","format","portable"' \
  PROJECT=shared-rules \
  APPLIES_TO='"all"' \
  APPLIES_TO_RATIONALE='Applies to all codebases, regardless of language.' \
  EXAMPLES='black ., eslint .'

echo

# 4. No Secrets in Repos
echo "Proposing: No Secrets in Repos"
make -f Makefile.ai ai-propose-rule \
  RULE_TYPE=security \
  DESCRIPTION='Never commit secrets or credentials to the repository.' \
  DIFF='---\ndescription: Never commit secrets or credentials to the repository.\nglobs: "**/*"\n---\n# No Secrets in Repos\n\n**Rule:**  \nSecrets, credentials, and API keys must never be committed to the repository.\n\n**Rationale:**  \n- Prevents accidental leaks and security incidents.\n\n**How to comply:**  \n- Use environment variables or secret management tools for sensitive data.\n- Add `.env` and similar files to `.gitignore`.\n\n**Examples:**\n- Use `os.environ["SECRET_KEY"]` in Python.\n- Use secret managers in CI/CD pipelines.' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"security"' \
  TAGS='"secrets","portable"' \
  PROJECT=shared-rules \
  APPLIES_TO='"all"' \
  APPLIES_TO_RATIONALE='Applies to all projects, regardless of language or stack.' \
  EXAMPLES='os.environ["SECRET_KEY"]'

echo

# 5. Relative Paths for Portability
echo "Proposing: Relative Paths for Portability"
make -f Makefile.ai ai-propose-rule \
  RULE_TYPE=portability \
  DESCRIPTION='Use relative paths for all project files and scripts.' \
  DIFF='---\ndescription: Use relative paths for all project files and scripts.\nglobs: "**/*"\n---\n# Use Relative Paths\n\n**Rule:**  \nAll scripts and code must use relative paths for accessing project files.\n\n**Rationale:**  \n- Ensures the project works on any system or environment.\n- Increases reproducibility and portability.\n\n**Examples:**\n- Use `fromhere::from_rproj("data/file.csv")` in R.\n- Use `os.path.join(os.path.dirname(__file__), "data", "file.csv")` in Python.' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"portability"' \
  TAGS='"paths","portable"' \
  PROJECT=shared-rules \
  APPLIES_TO='"all"' \
  APPLIES_TO_RATIONALE='Applies to all projects that need to be portable across systems.' \
  EXAMPLES='os.path.join(os.path.dirname(__file__), "data", "file.csv")'

echo "All portable rule proposals submitted." 
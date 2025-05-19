#!/bin/bash
set -e

# Batch import portable rules using Makefile.ai
echo "Importing: .mdc frontmatter rule"
make -f Makefile.ai ai-propose-portable-rule \
  RULE_TYPE=formatting \
  DESCRIPTION='All Cursor .mdc rule files must start with a YAML frontmatter block containing at least description and globs.' \
  DIFF='---\ndescription: <short description>\nglobs: <glob pattern>\n---\n' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"formatting","cursor","portable"' \
  TAGS='"formatting","cursor","portable"' \
  PROJECT=portable-rules

echo "Importing: .txt intermediate rule"
make -f Makefile.ai ai-propose-portable-rule \
  RULE_TYPE=formatting \
  DESCRIPTION='Use a .txt file as an intermediate step when creating new Cursor .mdc rule files to ensure frontmatter is preserved.' \
  DIFF='When adding a new rule:\n1. Create the rule content (including the required frontmatter) in a `.txt` file.\n2. Move or copy the `.txt` file into `.cursor/rules/` and rename it with a `.mdc` extension.\n3. Open the `.mdc` file in a plain text editor and confirm the frontmatter block is intact.' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"formatting","cursor","portable"' \
  TAGS='"formatting","cursor","portable"' \
  PROJECT=portable-rules

echo "Importing: pytest Makefile rule"
make -f Makefile.ai ai-propose-portable-rule \
  RULE_TYPE=testing \
  DESCRIPTION='All pytest executions must use Makefile targets and the -x flag for fail-fast.' \
  DIFF='- All pytest commands MUST run through Makefile targets (never run pytest directly).\n- Always use the -x flag for fail-fast.\n- Use Docker service names for connections (never localhost).\n- Use internal Docker network ports (never external mapped ports).\n- Required environment variables: ENVIRONMENT=test, POSTGRES_HOST=db-test, POSTGRES_PORT=5432, REDIS_HOST=redis-test, REDIS_PORT=6379.' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"testing","pytest","portable"' \
  TAGS='"testing","pytest","portable"' \
  PROJECT=portable-rules

echo "Importing: real vs mock services rule"
make -f Makefile.ai ai-propose-portable-rule \
  RULE_TYPE=testing \
  DESCRIPTION='Standardize handling of real vs mock services in tests, ensuring consistent interfaces and test isolation.' \
  DIFF='- Use real services in integration tests, mock services in unit tests.\n- Mock implementations must match real service interfaces exactly (method names, signatures, and behavior).\n- Use fixtures for service injection, not direct instantiation in tests.\n- Integration tests: use markers (e.g., @pytest.mark.real_service), connect to actual services, clean up after each test.\n- Unit tests: use mock services by default, focus on isolated component testing.\n- Test environment: use Docker service names (e.g., redis-test, db-test), never localhost.\n- Document mock limitations, do not add mock-specific features.' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"testing","mocking","portable"' \
  TAGS='"testing","mocking","portable"' \
  PROJECT=portable-rules

echo "Importing: health check best practices rule"
make -f Makefile.ai ai-propose-portable-rule \
  RULE_TYPE=api \
  DESCRIPTION='Liveness endpoints must not check dependencies; readiness endpoints must check all critical dependencies.' \
  DIFF='- Liveness endpoints (e.g., /health/liveness) must only check if the app process is running and must not fail due to external dependencies.\n- Readiness endpoints (e.g., /health/readiness) must check all critical dependencies (DB, Redis, etc.) and only return healthy if all are available.\n- Docker/Kubernetes configs must use the correct endpoint for each probe.' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"api","health","portable"' \
  TAGS='"api","health","portable"' \
  PROJECT=portable-rules

echo "Importing: Makefile target naming rule"
make -f Makefile.ai ai-propose-portable-rule \
  RULE_TYPE=automation \
  DESCRIPTION='All Makefile targets for external API actions must use a consistent prefix and be listed in the help section.' \
  DIFF='- All Makefile targets for external API actions must use a consistent prefix (e.g., ai-ide- or project-).\n- Targets should be named after the endpoint or action (e.g., ai-ide-propose-rule, ai-ide-review-code-file).\n- Update the help section in the Makefile to list all such targets.' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"automation","makefile","portable"' \
  TAGS='"automation","makefile","portable"' \
  PROJECT=portable-rules

echo "Importing: Makefile API endpoint documentation rule"
make -f Makefile.ai ai-propose-portable-rule \
  RULE_TYPE=automation \
  DESCRIPTION='All frequently used external API endpoints must have Makefile targets and be documented in onboarding.' \
  DIFF='- All frequently used external API endpoints must have corresponding Makefile targets.\n- The onboarding documentation must include a section listing these targets and their usage.\n- A Makefile target (e.g., ai-ide-openapi-spec) must exist to fetch and refresh the OpenAPI spec for the external API.\n- When new endpoints are added to the external API, update both the Makefile and documentation.' \
  SUBMITTED_BY=portable-rules-bot \
  CATEGORIES='"automation","api","portable"' \
  TAGS='"automation","api","portable"' \
  PROJECT=portable-rules 
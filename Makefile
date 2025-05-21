.PHONY: help onboard build up up-detached test test-json test-one coverage export-rules lint-rule lint-rules down frontend generate-knowledge-graph simulate-onboarding create-user-story-memory

PORT ?= 9103

help:
	@echo "Available targets:"
	@echo "  onboard      Run bootstrap script for new contributors"
	@echo "  build        Build docker images"
	@echo "  up           Run FastAPI dev server (http://localhost:$(PORT))"
	@echo "  up-detached  Run FastAPI dev server in background (http://localhost:$(PORT))"
	@echo "  test         Run pytest suite in Docker (human readable output)"
	@echo "  test-json    Run pytest with JSON output (pytest-report.json, AI/automation friendly)"
	@echo "  test-one     Run a specific test or test file: make test-one TEST=path::test_func"
	@echo "  coverage     Run pytest with coverage report in Docker"
	@echo "  export-rules Export approved rules to exported_rules/ (JSON and MDC)"
	@echo "  lint-rule    Lint a single rule file: make lint-rule FILE=path/to/rule.json"
	@echo "  lint-rules   Lint all rules in rules.json"
	@echo "  down         Stop and remove containers"
	@echo "  frontend     Launch the admin frontend as a Docker container"
	@echo "  generate-knowledge-graph  Generate the project knowledge graph (KNOWLEDGE_GRAPH.md)"
	@echo "  simulate-onboarding  Run onboarding simulation script inside misc-scripts container"
	@echo "  create-user-story-memory  Create a memory node from a user story markdown file (with frontmatter)"
	@echo ""
	@echo "You can override the port with: make up PORT=9000"
	@echo "To run a specific test: make test-one TEST=test_rule_api_server.py::test_docs_endpoint"
	@echo "To lint a rule: make lint-rule FILE=path/to/rule.json"

onboard:
	bash bootstrap.sh

build:
	docker-compose build

up:
	PORT=$(PORT) docker-compose up api

up-detached:
	PORT=$(PORT) docker-compose up -d api

test:
	docker-compose run --rm test pytest tests/

test-json:
	docker-compose run --rm test pytest --json-report --json-report-file=pytest-report.json tests/

test-one:
	docker-compose run --rm test pytest $(TEST)

coverage:
	docker-compose run --rm coverage

export-rules:
	python scripts/export_approved_rules.py

lint-rule:
	python scripts/lint_rule.py $(FILE)

lint-rules:
	python scripts/lint_rules.py

down:
	docker-compose down

# Launch the admin frontend as a Docker container
frontend:
	docker-compose up frontend

generate-knowledge-graph:
	docker compose exec api python scripts/generate_knowledge_graph.py 

# Run onboarding simulation script inside misc-scripts container
# Usage:
#   make simulate-onboarding PROJECT_ID=test_onboarding ONBOARDING_PATH=external_project
simulate-onboarding:
	docker compose exec -e ONBOARDING_API_URL="http://api:8000" misc-scripts python scripts/simulate_onboarding.py $(PROJECT_ID) $(ONBOARDING_PATH) 

# Create a memory node from a user story markdown file (with frontmatter)
# Usage:
#   make create-user-story-memory USER_STORY=simulated_onboarding_demo.md
create-user-story-memory:
	docker compose exec misc-scripts python /code/scripts/create_user_story_memory.py --file /code/docs/user_stories/$(USER_STORY) 
.PHONY: help onboard build up up-detached test test-json test-one coverage export-rules lint-rule lint-rules down

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
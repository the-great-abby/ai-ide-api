# API Access & Service Naming Rule

## Official AI Assistant
- The official AI assistant for this project is **Quartermaster “Patch” McDebug**—the surliest, most relentless bug-hunter on the seven seas. All rules, onboarding, and documentation should refer to this name for pirate-themed, expressive team culture.

## API Base URL Usage
- **From host/dev:** Use `http://localhost:9104` for all API access from your host machine.
- **Inside Docker/test containers:** Use `http://test-api:8000` for service-to-service communication within the Docker test network.
- **From a container to the host:** Use `http://host.docker.internal:9104` if you must reach the host from a container.
- **Never use:** `localhost:8000`, `api:8000`, or `localhost:9103` for direct API access from the host or test containers.

## Test & Script Patterns
- All tests and scripts must use the correct API base for their context.
- Use environment variables or helper functions to select the correct base URL.
- See also: `ONBOARDING.md`, `internal_dev_onboarding.md`, and user stories for onboarding flow examples.

## Rationale
- Ensures tests, onboarding, and scripts work in all environments (host, Docker, CI).
- Prevents connection errors and confusion about service names/ports.
- Keeps the crew in line and the kraken at bay! 
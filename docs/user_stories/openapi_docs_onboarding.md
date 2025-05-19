# User Story: OpenAPI Docs Onboarding for AI-IDE and Developers

## Motivation
As a new developer or AI IDE agent, I want a simple, reliable way to discover and access the API documentation (OpenAPI schema), so I can quickly understand available endpoints, request/response formats, and integrate or automate against the API.

## Actors
- New developer
- AI IDE agent
- Integrator

## Preconditions
- The API is running (locally or remotely)
- The codebase includes a Makefile with targets for API docs

## Step-by-Step Actions
1. **Fetch the OpenAPI docs using the Makefile:**
   ```bash
   make -f Makefile.ai ai-docs
   ```
   - This command will print the OpenAPI documentation endpoint or return the docs directly if the API is running.

2. **Alternatively, access the interactive docs in your browser:**
   - Visit: [http://localhost:9103/docs](http://localhost:9103/docs)
   - This provides a human-friendly UI for exploring and testing endpoints.

3. **For programmatic access:**
   - Fetch the raw OpenAPI schema:
     ```bash
     curl http://localhost:9103/openapi.json
     ```
   - Use this JSON for client code generation, API exploration, or integration tests.

4. **If the API is not running:**
   - Start all services:
     ```bash
     make -f Makefile.ai ai-up
     ```

## Expected Outcomes
- The user or AI IDE can easily fetch and view the latest OpenAPI docs.
- The process is standardized and referenced in onboarding and Makefile help.
- API consumers can generate clients, test endpoints, or explore the API interactively.

## Best Practices
- Always use the Makefile target (`ai-docs`) for consistency and automation.
- Reference this workflow in onboarding and developer docs.
- Keep the OpenAPI schema up to date with code changes.

## References
- Makefile.ai targets: `ai-docs`, `ai-onboarding-help`
- [ONBOARDING_OTHER_AI_IDE.md](../ONBOARDING_OTHER_AI_IDE.md) 
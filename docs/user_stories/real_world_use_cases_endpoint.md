# User Story: Real-World Use-Cases Endpoint for AI IDE API

## Motivation
Developers and integrators need a way to programmatically discover real-world use-cases and example workflows for the AI IDE API. This will help other AI IDEs, developer tools, and automation systems to display, recommend, and inspire new integrations or features based on proven patterns.

## Actors
- API consumers (developers, integrators, AI agents)
- AI IDE maintainers
- Documentation and onboarding systems

## Preconditions
- The AI IDE API is running and accessible.
- There are documented use-cases and example workflows available in the system (static or dynamic).

## Step-by-Step Actions
1. A client sends a GET request to the new endpoint (e.g., `/api/use-cases` or `/use-cases`).
2. The API returns a structured JSON response containing:
    - Use-case titles
    - Descriptions
    - Example API calls or workflows (with sample payloads, if relevant)
3. The client displays or processes these use-cases for end-users, onboarding, or automation.

## Expected Outcomes
- Clients can programmatically retrieve a list of real-world use-cases and example workflows.
- The endpoint returns up-to-date, structured data suitable for display or further automation.
- New users and integrators are inspired and guided by concrete examples.

## Best Practices
- Ensure the endpoint is well-documented in the OpenAPI schema.
- Keep use-cases and examples up to date as the API evolves.
- Provide both simple and advanced examples to cover a range of user needs.
- Consider versioning the endpoint if use-case structure changes.

## Example Response
```json
[
  {
    "title": "Automated Project Rule Suggestion",
    "description": "Suggest rules for a new project based on its README and codebase.",
    "example_workflow": [
      {"endpoint": "/rules/suggest", "method": "POST", "payload": {"project_id": "...", "readme": "..."}}
    ]
  },
  {
    "title": "Memory Graph Search",
    "description": "Search the memory graph for relevant nodes using natural language.",
    "example_workflow": [
      {"endpoint": "/memory/nodes/search", "method": "POST", "payload": {"text": "How do I backup my database?"}}
    ]
  }
]
```

## References
- Enhancement ID: 236c2137-fd92-491d-bf6c-549b139ea750
- Related documentation: [OpenAPI docs], [Onboarding guides] 
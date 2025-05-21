# Rule: User Story Memory Creation

## Motivation
To ensure every new workflow, automation, or feature is discoverable and context-rich, we automatically create a memory node in the AI IDE API whenever a user story is created or updated.

## Enforcement
- When a user story is created or updated in `docs/user_stories/`, a script or automation should:
  - Parse the user story frontmatter for metadata, tags, and related files.
  - Generate a summary of the user story (using LLM if needed).
  - Collect a list of related files, endpoints, and onboarding paths.
  - Optionally, include the git commit summary.
  - Submit this information to the AI IDE API as a new memory node using the rich schema.
  - Tag memories as `internal` or `external` based on the `visibility` field in the frontmatter.

## Example Workflow
1. Create or update a user story (e.g., `docs/user_stories/simulated_onboarding_demo.md`) with the required frontmatter.
2. Run `make create-user-story-memory USER_STORY=simulated_onboarding_demo.md` (or via pre-commit/CI automation).
3. The script:
   - Reads the user story and parses the frontmatter.
   - Gathers related files and endpoints.
   - Calls the AI IDE API to create a memory node with this info.
   - If the summary is missing, uses an LLM to generate one.

## Memory Schema
```
{
  "name": "Simulated Onboarding Demo",
  "type": "user_story",
  "summary": "How to simulate onboarding for any path using scripts and API.",
  "description": "Full markdown or HTML content of the user story.",
  "files": [
    "docs/user_stories/simulated_onboarding_demo.md",
    "scripts/simulate_onboarding.py",
    "Makefile"
  ],
  "endpoints": [
    "/onboarding/init",
    "/onboarding/progress/{project_id}",
    "/onboarding-docs",
    "/onboarding/user_story/{path}"
  ],
  "tags": ["external", "onboarding", "automation"],
  "created_by": "abby",
  "created_at": "2024-06-07T12:34:56Z",
  "updated_at": "2024-06-07T12:34:56Z",
  "related_stories": ["external_project_onboarding"],
  "git_commit": "abc123",
  "visibility": "external",
  "onboarding_paths": ["external_project", "internal_dev"],
  "reviewed": true,
  "review_notes": "Tested in onboarding simulation, works as expected."
}
```

## Best Practices
- Always specify related files, endpoints, and onboarding paths in the user story frontmatter.
- Use clear, concise summaries and tag visibility appropriately.
- Reference the memory node in code reviews and onboarding docs.
- Tag most documentation as `internal` by default; curate and tag external-facing docs as `external`.
- Embeddings/vectors are handled on the Ollama functions side and should not be returned in memory search results or documentation.

## References
- `docs/user_stories/_frontmatter_template.md`
- AI IDE API `/memory` endpoint
- LLM endpoint for summary generation
- Onboarding paths for cross-linking 
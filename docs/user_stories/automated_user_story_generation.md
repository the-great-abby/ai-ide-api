# User Story: Automated User Story Generation for Key DevOps Events

## Motivation
As a developer, SRE, or AI agent, I want user stories to be automatically generated for all key project events (troubleshooting, onboarding, code review, enhancements), so that our documentation, knowledge base, and onboarding materials are always up-to-date, searchable, and actionable—with minimal manual effort.

## Actors
- Developer
- SRE/Support Engineer
- AI IDE agent
- Project Lead

## Preconditions
- The ai-ide-api is running and accessible.
- LLM endpoints (e.g., `/review-code-files-llm`) are available for summarization.
- Memory logging is enabled via `/memory/nodes`.
- Scripts or Makefile targets exist (or will be created) to automate user story generation.

## Step-by-Step Actions

1. **Trigger Event**
   - A key event occurs, such as:
     - A troubleshooting step is logged
     - An onboarding step is completed
     - A code review or enhancement is performed

2. **Gather Context**
   - Collect relevant details:
     - For troubleshooting: error, actions, outcome
     - For onboarding: step, purpose, result
     - For code review: files, feedback, improvements
     - For enhancements: motivation, implementation, result

3. **Generate User Story Draft**
   - Use a standard template or prompt.
   - Optionally, call the LLM endpoint (e.g., `/review-code-files-llm`) to generate a natural language summary.
   - Example template:
     ```markdown
     # User Story: [Title]
     ## Motivation
     [Why this was needed]
     ## Steps
     [What was done]
     ## Outcome
     [Result]
     ```

4. **Save the User Story**
   - Write the draft as a markdown file in `docs/user_stories/`.
   - Optionally, log a reference to the user story in memory (namespace: `user_story`).

5. **Confirm & Notify**
   - Ensure the user story is saved and (optionally) notify the team or log the event.

6. **Repeat**
   - For each new event, repeat the process.

## Expected Outcomes
- All key events are documented as user stories, automatically and consistently.
- The team can search, review, and learn from a living, up-to-date knowledge base.
- Onboarding, troubleshooting, and retrospectives are improved with rich, contextual user stories.
- LLM-generated summaries provide high-quality, human-readable documentation.

## Best Practices
- Keep templates simple and adaptable for each event type.
- Use the LLM for complex or multi-file summaries.
- Regularly review and curate user stories for clarity and relevance.
- Integrate user story generation into CI/CD, onboarding, and troubleshooting workflows.

## References
- [ai-ide-api OpenAPI docs](http://localhost:9103/docs)
- [LLM Code Review User Story](./ai_augmented_code_review_full_workflow.md)
- [Troubleshooting Memory Logging User Story](./troubleshooting_memory_logging.md) 
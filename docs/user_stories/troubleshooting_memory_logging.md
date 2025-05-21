# User Story: Automated Logging of Troubleshooting Steps to ai-ide-api Memory

## Motivation
As a developer or AI assistant, I want every troubleshooting step to be automatically logged to the ai-ide-api memory, so that I can track, search, and analyze the project's troubleshooting history for better knowledge sharing and faster problem resolution.

## Actors
- Developer
- AI IDE agent
- SRE/Support Engineer

## Preconditions
- The ai-ide-api is running and accessible.
- An admin token is available for authentication.
- The `/memory/nodes` endpoint is enabled.
- (Optional) The `/review-code-files-llm` endpoint is available for generating LLM-based summaries.

## Step-by-Step Actions

1. **Trigger a Troubleshooting Step**
   - Encounter an error, warning, or unexpected behavior.
   - Begin diagnosing or resolving the issue.

2. **Summarize the Step**
   - Write a brief summary including:
     - The issue encountered.
     - Actions taken.
     - Outcome or next steps.
   - **Optionally:** Use the `/review-code-files-llm` endpoint to generate an LLM-based summary of the troubleshooting step or related code files.

3. **Log the Step to Memory**
   - POST to `/memory/nodes` with:
     ```json
     {
       "namespace": "troubleshooting",
       "content": "Brief summary of the troubleshooting step"
     }
     ```
   - Use the admin token for authentication.

4. **Confirm Logging**
   - Ensure the API returns a success response.
   - Optionally, notify the user or team that the step was logged.

5. **Repeat**
   - For each new troubleshooting step, repeat the process.

## Expected Outcomes
- All troubleshooting steps are persistently logged.
- The team can search, review, and learn from past troubleshooting efforts.
- Onboarding and support are improved with a searchable troubleshooting history.
- LLM-generated summaries can be included for richer context and automated insights.

## Best Practices
- Keep summaries concise but informative.
- Use the `meta` field for additional context if needed.
- Regularly review logged troubleshooting steps for patterns and improvements.
- Leverage the `/review-code-files-llm` endpoint to generate high-quality summaries when appropriate.

## References
- [ai-ide-api OpenAPI docs](http://localhost:9103/docs)
- [Makefile.ai targets] (if you automate this via Makefile or scripts)
- [LLM Code Review User Story](./ai_augmented_code_review_full_workflow.md) 
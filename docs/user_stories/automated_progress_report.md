# User Story: Automated Progress Reporting and Memory Integration

## Motivation
To ensure continuous, high-quality documentation and architectural awareness, we want to automatically generate progress reports from code changes. These reports should be summarized by an LLM, categorized, and stored as memory nodes with relationships, enabling both humans and AI agents to track, review, and improve the project's evolution.

## Actors
- Developer
- RabbitMQ Worker
- LLM (Ollama Functions)
- Memory System
- Human Reviewer (optional, for open questions)

## Preconditions
- Codebase is under git version control.
- RabbitMQ and Ollama LLM functions are available.
- Memory system is operational and accessible via API or direct DB access.

## Steps
1. A scheduled RabbitMQ worker runs every hour.
2. The worker computes a git diff between the last processed commit and HEAD.
3. If changes are detected:
    - The worker packages the diff, commit messages, and metadata.
    - The worker sends this data to the Ollama LLM for summarization and categorization.
    - The LLM returns a summary, categories, tags, and open questions.
    - The worker creates memory nodes for the summary, categories, and questions, establishing relationships between them and related commits/files.
    - If no memory template exists, the LLM proposes one, which is saved for future use.
4. Open questions are flagged for human or automated follow-up.
5. (Optional) Another worker or human reviews and tidies up memory nodes, adding tags or relationships as needed.

## Expected Outcomes
- Automated, opinionated progress reports are generated and stored as memory nodes.
- Open questions and design uncertainties are surfaced for review.
- The memory system is continuously updated with categorized, connected knowledge.
- Future workers or humans can easily review, tag, and connect memory items.

## Best Practices
- Use a consistent memory node template for summaries, questions, and categories.
- Track the last processed commit in a durable, queryable location (e.g., memory node or DB).
- Ensure LLM prompts are clear and structured for reliable output.
- Periodically review open questions and uncategorized nodes. 
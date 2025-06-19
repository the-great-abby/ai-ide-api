---
title: Progress Report & LLM Summarization Workflow
status: draft
---

# User Story: Progress Report & LLM Summarization Workflow

## Motivation
Enable automated, AI-powered summaries of code changes (git diffs) for improved project visibility, technical documentation, and onboarding. This workflow ensures that every code change can be summarized and stored as a memory node, making it easy for team members and AI agents to understand recent project activity.

## Actors
- **Developer**: Triggers progress report jobs and reviews summaries.
- **Worker Service**: Processes jobs, fetches git diffs, calls the LLM, and creates memory nodes.
- **LLM Service (Ollama)**: Provides technical summaries of git diffs.
- **API Service**: Stores and serves memory nodes.
- **Database**: Persists memory nodes and tokens.
- **RabbitMQ**: Queues jobs for background processing.

## Preconditions
- All required containers/services are running:
  - **api**: FastAPI backend (port 9103)
  - **db**: PostgreSQL database
  - **rabbitmq**: Message broker
  - **worker**: Background job processor (with valid admin token)
  - **ollama-functions**: LLM API for summarization
  - **misc-scripts**: For triggering jobs (e.g., progress report)
- Valid admin API token is available for the worker and API requests.
- The git repository is initialized and has recent commits.

## Step-by-Step Actions
1. **Start All Required Services**
   ```bash
   docker compose up -d api db rabbitmq worker ollama-functions misc-scripts
   # or using Makefile targets:
   make -f Makefile.ai-dev dev-up
   make -f Makefile.ai-dev dev-worker-up
   ```
2. **Trigger a Progress Report Job**
   ```bash
   make -f Makefile.ai-misc trigger-progress-report
   # or manually:
   docker compose exec misc-scripts python3 /scripts/publish_progress_report_job.py
   ```
3. **Worker Processes the Job**
   - Fetches the latest git diff.
   - Calls the LLM (Ollama) for a technical summary.
   - Creates a new memory node in the API with the summary and metadata.
4. **Verify the Results**
   - Query the API for new memory nodes:
     ```bash
     curl -H "Authorization: Bearer <admin_token>" "http://localhost:9103/memory/nodes?namespace=progress_reports" | jq .
     ```
   - Check worker and ollama logs for errors or successful processing.

## Makefile Usage
Trigger the progress report worker using the following Makefile targets:

```bash
# Trigger a progress report job
make -f Makefile.ai memory-trigger-progress

# Alternative trigger method (from misc-scripts container)
make -f Makefile.ai misc-trigger-progress-report

# Monitor worker logs during progress report processing
make -f Makefile.ai memory-worker-logs

# Check progress report status and queue
make -f Makefile.ai memory-status-report

# View recent progress report memory nodes
make -f Makefile.ai memory-list-nodes-summary
```

**Note:** The progress report worker automatically fetches the latest git diff and creates a memory node with the LLM-generated summary.

## Expected Outcomes
- A new memory node is created for each progress report, containing a detailed LLM-generated summary of the latest git diff.
- The summary is accessible via the API and can be used for documentation, onboarding, or further automation.

## Best Practices
- Always ensure all required containers are running before triggering jobs.
- Use Makefile targets for consistent environment setup and job execution.
- Monitor logs for errors, especially after code or environment changes.
- Keep admin tokens secure and up to date in the worker environment.
- Regularly clean up unused containers and volumes to avoid resource conflicts.

## References
- [Testing Workflow Guidelines](../onboarding/TESTING_WORKFLOW.md)
- [AI-Optimized Makefile Targets](../onboarding/automation_and_makefile_best_practices.md)
- [LLM Service Setup](../onboarding/ONBOARDING_INTERNAL.md) 
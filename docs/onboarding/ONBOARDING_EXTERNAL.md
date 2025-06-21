## 🚀 Automated Onboarding: First-Class Self-Service for External Users

To make onboarding smooth and easy, you can download and run our automated onboarding scripts:

- [Download Python onboarding script](../onboarding/scripts/onboard_external.py)  
  Or via API: `GET /onboarding/scripts/onboard_external.py`
- [Download Bash onboarding script](../onboarding/scripts/onboard_external.sh)  
  Or via API: `GET /onboarding/scripts/onboard_external.sh`

**How to use:**
1. Download the script (Python or Bash) to your machine.
2. Run the script and follow the prompts (API URL, project name, onboarding path).
3. The script will generate your API token, register your project, and guide you to the next steps.
4. Your token will be saved in `.apitoken` for use in future API calls.
5. **Optional**: The script will also generate Docker Compose files for background workers.

**Generated Files:**
- `Makefile.external` - All API interaction commands
- `docker-compose.external.yml` - RabbitMQ and worker services
- `worker/Dockerfile` - Worker container configuration
- `worker/requirements.txt` - Python dependencies for workers
- `setup-workers.sh` - Automated worker setup script

**Background Workers (Optional):**
The onboarding script generates Docker Compose files that set up:
- **RabbitMQ** for message queuing
- **Worker containers** for background processing
- **Project-specific network** (`{project-name}-memory-rabbitmq`)

Workers handle:
- Memory enrichment and cleanup
- Similarity pruning
- Git history analysis
- Progress reporting
- **Git diff summarization** (via API endpoint)

**Note:** External workers access LLM functionality through the main AI-IDE-API endpoints, ensuring secure and controlled access to Ollama Functions.

To start workers:
```bash
./setup-workers.sh
# or manually:
docker-compose -f docker-compose.external.yml up -d
```

Workers connect to the AI-IDE-API at `host.docker.internal:9103` and process jobs from the RabbitMQ queues.

If your workflow or features require the memorydb, make sure to run its migrations:
```bash
make -f Makefile.ai-db ai-memorydb-migrate
```
This ensures the memorydb schema is up to date and ready for use.

This process is fully self-service and designed for a first-class external onboarding experience!

## 🚀 Advanced Feature: Flexible, Extensible Memory System

This project's memory system isn't just for rules and proposals—it can store, search, and relate any type of knowledge or event (like feedback, bug reports, meeting notes, experiments, and more). The system is designed to scale as your needs grow, supporting custom types, relationships, and retention policies.

Learn more about how to leverage and extend this feature in the [Expanding the Memory System Guide](EXPANDING_MEMORY_SYSTEM.md). 
# User Story: Ollama Gateway Support for LLM-Based Functions

## Motivation
To enable LLM-powered features (such as rule suggestion, code review, or AI assistants), our service must be able to communicate with an Ollama backend via a dedicated gateway service. Ensuring the Ollama gateway is available, healthy, and using the correct model is critical for reliability and developer productivity.

---

## Actors
- Developer
- System Administrator
- CI/CD Pipeline

---

## Preconditions
- Ollama is installed and the required model is pulled (e.g., `llama3.1:8b-instruct-q6_K`).
- Docker and Makefile.ai are available.
- The `ollama-functions` gateway service is defined in `docker-compose.yml` and built.
- The main service is configured to use the Ollama gateway for LLM requests.

---

## Step-by-Step Actions

### 1. Ensure the Ollama Model is Pulled
```bash
make -f Makefile.ai ai-ollama-pull-model
```
- Downloads the required model if not already present.

### 2. Start the Ollama Backend (Host)
```bash
make -f Makefile.ai ai-ollama-serve-docker-gateway-bg
```
- Runs `ollama serve` in the background, accessible to Docker containers.

### 3. Start the Ollama Gateway Service (Docker Compose)
```bash
make -f Makefile.ai ai-up-ollama-functions
```
- Brings up the `ollama-functions` service for API access.

### 4. Check Service Health
```bash
make -f Makefile.ai ai-ollama-functions-health
```
- Should return `{ "status": "ok" }` if the gateway is running.

### 5. (Optional) View Logs
```bash
make -f Makefile.ai ai-ollama-functions-logs
```
- Shows the last 100 lines of gateway logs for troubleshooting.

---

## Expected Outcomes
- The Ollama backend and gateway are running and healthy.
- The main service can make LLM requests via the gateway.
- Developers and CI/CD can rely on a consistent, automated setup for LLM-powered features.

---

## Best Practices
- Always check the health of the Ollama gateway before running LLM-dependent features or tests.
- Automate the setup in onboarding scripts or CI/CD pipelines.
- Document the required model and update as new models are adopted.
- Use background targets for long-running services to avoid blocking the shell.
- Regularly monitor logs for errors or model updates.

---

## References
- `Makefile.ai` targets: `ai-ollama-pull-model`, `ai-ollama-serve-docker-gateway-bg`, `ai-up-ollama-functions`, `ai-ollama-functions-health`, `ai-ollama-functions-logs`
- `docker-compose.yml` for service definitions
- [llm_onboarding.md](llm_onboarding.md) for LLM integration details

---

## Troubleshooting & Additional Makefile Targets

### Common Issues & Solutions

- **Ollama gateway health check fails**
  - Ensure both the backend and gateway are running:
    ```bash
    make -f Makefile.ai ai-ollama-serve-docker-gateway-bg
    make -f Makefile.ai ai-up-ollama-functions
    make -f Makefile.ai ai-ollama-functions-health
    ```
- **Model not found or outdated**
  - Pull or update the model:
    ```bash
    make -f Makefile.ai ai-ollama-pull-model
    ```
- **Gateway or backend not responding**
  - Restart the services:
    ```bash
    make -f Makefile.ai ai-restart-ollama-functions
    make -f Makefile.ai ai-ollama-restart-docker-gateway
    ```
- **Stop or remove the gateway service**
  - Stop or remove the container:
    ```bash
    make -f Makefile.ai ai-stop-ollama-functions
    make -f Makefile.ai ai-down-ollama-functions
    ```
- **Kill or restart the Ollama backend (host)**
  - Kill or restart the backend process:
    ```bash
    make -f Makefile.ai ai-ollama-kill
    make -f Makefile.ai ai-ollama-restart-docker-gateway
    ```
- **View logs for debugging**
  - Gateway logs:
    ```bash
    make -f Makefile.ai ai-ollama-functions-logs
    ```
  - Ollama backend logs (if running in background):
    ```bash
    make -f Makefile.ai ai-ollama-logs
    ```

### Reference: Makefile Targets for Ollama Functions
- `ai-ollama-pull-model` — Download/update the Ollama model
- `ai-ollama-serve-docker-gateway` — Start backend in foreground
- `ai-ollama-serve-docker-gateway-bg` — Start backend in background
- `ai-ollama-kill` — Kill all running Ollama backend processes
- `ai-ollama-restart-docker-gateway` — Restart backend on Docker gateway
- `ai-up-ollama-functions` — Start the gateway service (Docker Compose)
- `ai-restart-ollama-functions` — Rebuild and restart the gateway service
- `ai-stop-ollama-functions` — Stop the gateway service
- `ai-down-ollama-functions` — Remove the gateway service container
- `ai-ollama-functions-health` — Health check for the gateway
- `ai-ollama-functions-logs` — View gateway logs
- `ai-ollama-logs` — View Ollama backend logs (background run) 
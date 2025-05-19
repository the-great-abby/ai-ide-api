# User Story: Containerized LLM Rule Suggestion Workflow

**Title:**  
LLM Rule Suggestion via Docker Compose

**As a** developer or reviewer,  
**I want** to generate rule proposals using the LLM from within a Docker Compose service,  
**So that** the process is reproducible, networked correctly, and works in all environments.

---

## Workflow Steps

1. **Start Ollama on the host, listening on all interfaces:**
   ```bash
   make -f Makefile.ai ai-ollama-serve-docker-gateway
   ```
   - This ensures the LLM service is accessible to containers via `host.docker.internal`.

2. **Rebuild the ollama-functions image if you've changed scripts or dependencies:**
   ```bash
   make -f Makefile.ai ai-build-ollama-functions-service
   ```

3. **Run the LLM rule suggestion from within the Docker Compose network:**
   ```bash
   OLLAMA_URL=http://host.docker.internal:11434/api/generate make -f Makefile.ai ai-suggest-llm-rules-docker
   ```
   - This uses `docker compose run` to execute the script inside the `ollama-functions` service, ensuring correct network access and environment.

4. **Review the generated rule proposals and integrate as needed.**

---

## Troubleshooting

- If you see "No such file or directory," ensure the script is in the correct directory (`scripts/`) and the image is rebuilt.
- If you see connection errors, ensure Ollama is running and accessible on the host.
- If the LLM output is not valid JSON, improve the prompt or add post-processing to handle Markdown/plain text.
- Do **not** use `localhost` from within the container; use `host.docker.internal`.

---

## Why This Matters

- Running via Docker Compose ensures the container is attached to the correct network and can resolve service names.
- This approach is portable, reproducible, and works for all team members regardless of host OS. 
## Ollama Server Setup for Integration

To ensure that the AI-IDE API and integration tests can connect to the Ollama embedding server, always launch Ollama using the provided Makefile target:

```bash
make -f Makefile.ai ai-ollama-serve-docker-gateway
```

This will start Ollama with `OLLAMA_HOST=0.0.0.0`, making it accessible to Docker containers. **Do not add `--host` or `--port` flags**—the environment variable is sufficient for most setups and is compatible with the current Ollama version.

### If you need a specific port (advanced):
- By default, Ollama uses port 11434. If you need to change the port, consult the Ollama documentation for your version. Most users should not need to change this.

**Note:**
- If you see errors like `unknown flag: --host` or `unknown flag: --port`, your Ollama version does not support those flags. Use only the environment variable as shown above.
- You can check the Ollama server log for the listening address and port.
- If you change the port, update your integration test and any service that connects to Ollama accordingly.

## Stopping and Restarting the Ollama Server

If you need to stop the Ollama server (for example, to resolve port conflicts or restart with new settings), use the provided Makefile target:

```bash
make -f Makefile.ai ai-ollama-kill
```

This will terminate all running Ollama server processes.

To restart the server:

```bash
make -f Makefile.ai ai-ollama-serve-docker-gateway
```

**Troubleshooting:**
- If you encounter errors about the port already being in use, run `ai-ollama-kill` before starting a new instance.
- If you change the port or host, update your integration tests and Makefile targets accordingly.
- If you see errors about unknown flags, remove `--host` and `--port` from your Makefile or command. 
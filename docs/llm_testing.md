# LLM-Related Testing: Ollama Functions Server

*Maintained by Doc the Medic*

## Overview
Some tests (especially those involving LLM or code review endpoints) require the Ollama Functions server to be running. If this service is not available, LLM-related tests will fail with connection or timeout errors.

## How to Start the Ollama Functions Server for Testing

To start the Ollama Functions server in the test environment:

```sh
make -f Makefile.ai-test ai-up-test-ollama-functions
```

To stop the server:

```sh
make -f Makefile.ai-test ai-down-test-ollama-functions
```

## Troubleshooting
- If you see errors about LLM endpoints or code review failing, make sure the Ollama Functions server is running.
- For dev (non-test) environment, use the corresponding dev Makefile targets.

## References
- See Makefile.ai-test for the latest targets.
- For more help, contact Doc the Medic or check this doc. 
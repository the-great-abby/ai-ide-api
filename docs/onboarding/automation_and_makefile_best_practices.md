# Automation & Makefile Best Practices for AI IDE Projects

## Why Automate?

Automation is at the heart of modern development for several reasons:

- **Reproducibility:** The primary motivator—automation helps you remember and reliably rebuild complex commands and workflows. You can always get back to a known good state.
- **Consistency:** Automated targets ensure that every run is the same, reducing "it works on my machine" problems.
- **Speed:** Once automated, tasks run much faster than manual steps, and you can chain them together for even greater efficiency.
- **AI/Agent Compatibility:** The `.ai` Makefile signifier allows for AI-specific commands, letting the system move faster and more safely without interfering with standard Makefile targets. This enables both humans and AI agents to interact with the project in a predictable, discoverable way.
- **Debuggability:** When a target fails, both humans and AI agents can review, rerun, and debug the exact command sequence.
- **Discoverability:** Makefiles serve as living documentation for project workflows, making it easy for new contributors (and AI agents) to learn how to operate the system.

## How Makefile & Automation Help Humans and AI Agents

- **Memory & Reuse:** The Makefile allows the system (and you) to remember how to perform successful commands, making it easy to repeat or adapt them.
- **Debugging:** When a target fails, the system can debug and retry, and humans can review the command history for insight.
- **Efficiency:** AI agents can execute Makefile targets directly, reducing token/memory/bandwidth usage and increasing speed.
- **Transparency:** Humans can review Makefile targets to understand or audit what the AI is doing.
- **Extensibility:** New targets can be added for new workflows, and user stories can be referenced for onboarding and documentation.

## External Project Onboarding: Pulling Down the API Spec/Docs

For external projects integrating with the AI IDE API, the first step should be to download the OpenAPI spec and documentation from the API server. This ensures you have the latest interface and can generate clients or review endpoints as needed.

**Recommended Step:**

1. **Download the API spec/docs:**
   - If running locally: `curl http://localhost:9103/openapi.json -o openapi.json`
   - If running in Docker: `curl http://host.docker.internal:9103/openapi.json -o openapi.json`
   - (You can also access `/docs` for the Swagger UI.)
2. **Review this onboarding documentation** (this file) before generating tokens or accessing other parts of the system.

## API-Only Access: Ensuring Onboarding is Available

If you only have access to the project via the AI IDE API (e.g., at `localhost:9103` or `host.docker.internal:9103`), you should:

- **Download and review this onboarding documentation** as your first step. This will help you understand the automation philosophy, Makefile usage, and integration patterns before you start interacting with the API.
- **Optionally, make this doc downloadable via a dedicated endpoint** (e.g., `/onboarding-docs`) so users and agents can fetch it programmatically.

**Encouragement:**
- Reviewing this doc before gathering specs/docs will help you get the most out of the system and avoid common pitfalls.
- If you have suggestions for improving onboarding, please contribute or open an issue! 
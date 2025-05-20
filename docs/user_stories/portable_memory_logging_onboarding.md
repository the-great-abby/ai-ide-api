# User Story: Portable AI-Powered Memory Logging & Git Diff Summarization

## Motivation
As a developer or team, I want to easily enable automated memory logging and LLM-powered git diff summarization in any project, so that I can:
- Track important code changes and lessons across all my repos
- Leverage AI to generate detailed, technical summaries of changes
- Keep project knowledge organized, searchable, and portable

---

## Actors
- Developer
- Maintainer
- Onboarding team member
- CI/CD pipeline

---

## Preconditions
- Access to a running Memory API and LLM Summarization API (can be local or shared)
- Docker (optional, for running services)
- Makefile and scripts copied or symlinked into the repo

---

## Setup Steps
1. **Copy or symlink the following into your repo:**
   - `scripts/create_memory.py`, `scripts/summarize_git_diff.py`, and any helper scripts
   - The relevant Makefile targets (see `Makefile.memory` or copy from a reference repo)
2. **Set environment variables as needed:**
   - `PROJECT` (defaults to repo name)
   - `NAMESPACE` (defaults to project)
   - `MEMORY_API_URL` (defaults to `http://localhost:9103/memory/nodes`)
   - `LLM_API_URL` (defaults to `http://localhost:9104/summarize-git-diff`)
   - `DIFFS_DIR` (defaults to `diffs`)
   - Use a `.env` file or export in your shell for convenience
3. **Start or connect to the required services:**
   - Memory API and LLM Summarization API (Ollama Functions)
   - Use Docker Compose or point to a shared instance
4. **Run the workflow:**
   ```bash
   make -f Makefile.memory ai-memory-log-git-diff
   ```
   - This will generate a git diff, summarize it with the LLM, store the summary and a reference to the diff file as a memory node

---

## Quick Start Example
```bash
# Clone or copy scripts and Makefile.memory
cp -r ../ai-ide-api/scripts ./scripts
cp ../ai-ide-api/Makefile.memory ./Makefile.memory

# (Optional) Set environment variables
export PROJECT=my-other-repo
export MEMORY_API_URL=http://shared-server:9103/memory/nodes

# Log a git diff as a memory node
make -f Makefile.memory ai-memory-log-git-diff
```

---

## Best Practices
- Use environment variables for all project-specific values
- Namespace memory nodes by project for easy filtering
- Store only references to large diffs, not the full content
- Document the workflow in your project's README for discoverability
- Use `.env` files for local overrides
- Reference this user story in onboarding docs and code reviews

---

## References
- See the project `README.md` for a copy-paste quick start
- For advanced usage, see the Makefile and scripts for all available targets and options
- For troubleshooting, check the logs of the Memory API and LLM Summarization API

---

**This workflow makes AI-powered, portable memory logging available to all your projects—just copy, configure, and go!** 
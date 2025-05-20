# User Story: Automated Git Diff Memory Logging with LLM Summaries

## Motivation
As a developer or maintainer, I want to automatically log code changes (git diffs) as memory nodes, with detailed LLM-generated summaries, so that I can:
- Track important changes and their context over time
- Quickly review what changed and why
- Enable onboarding, troubleshooting, and knowledge sharing

---

## Actors
- Developer
- Maintainer
- CI/CD pipeline (optional)

---

## Preconditions
- The AI IDE API and Ollama Functions services are running
- The Makefile.ai target `ai-memory-log-git-diff` is available
- You have local git changes (committed, staged, or unstaged)

---

## Step-by-Step Actions

### 1. Get a Diff of Your Changes
- **All changes since last commit (work in progress):**
  ```bash
  git diff HEAD
  ```
- **Only staged changes:**
  ```bash
  git diff --cached
  ```
- **Only unstaged changes:**
  ```bash
  git diff
  ```
- **Between any two commits/branches:**
  ```bash
  git diff <commit1>..<commit2>
  ```

### 2. Log the Diff as a Memory Node
- **Default (all changes since last commit):**
  ```bash
  make -f Makefile.ai ai-memory-log-git-diff DIFF_RANGE=HEAD
  ```
- **Custom range:**
  ```bash
  make -f Makefile.ai ai-memory-log-git-diff DIFF_RANGE=main..feature-branch
  ```
- **Concise summary:**
  ```bash
  make -f Makefile.ai ai-memory-log-git-diff DIFF_RANGE=HEAD CONCISE=1
  ```
- **Custom name/observation/namespace:**
  ```bash
  make -f Makefile.ai ai-memory-log-git-diff DIFF_RANGE=HEAD NAME="wip-20240520" OBSERVATION="WIP changes before refactor" NAMESPACE="ai-ide-api"
  ```

### 3. What Happens
- The Makefile target:
  1. Generates the git diff for the specified range
  2. Calls the `/summarize-git-diff` endpoint (LLM, verbose by default)
  3. Combines the summary, diff, and range into a meta field
  4. Creates a memory node with all this information

---

## Expected Outcomes
- A new memory node is created, containing:
  - The git diff
  - An LLM-generated summary (detailed or concise)
  - Metadata (diff range, timestamp, etc.)
- You can search, review, and share these memories for onboarding, retrospectives, or debugging

---

## Best Practices
- Use this workflow for major merges, releases, or refactors
- Add meaningful names and observations for easier search
- Use concise summaries for small changes, verbose for major ones
- Regularly review memory nodes to build project knowledge

---

## References
- Makefile.ai: `ai-memory-log-git-diff`
- API: `/summarize-git-diff`, `/memory/nodes` 
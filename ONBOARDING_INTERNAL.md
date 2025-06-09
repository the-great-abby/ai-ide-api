# Internal Developer Onboarding

## 🏴‍☠️ Quickstart (For New Crew)

1. Clone the repo:
   ```bash
   git clone <repo-url>
   cd ai-ide-api
   ```
2. Start the environment:
   ```bash
   make -f Makefile.ai ai-env-up
   ```
3. Run the database migrations:
   ```bash
   make -f Makefile.ai ai-db-migrate
   make -f Makefile.ai ai-memorydb-migrate
   ```
4. Run the tests:
   ```bash
   make -f Makefile.ai ai-test
   ```
5. Or, run everything in one go:
   ```bash
   make -f Makefile.ai quickstart
   ```
6. If you see green, you're ready to code! If not, see Troubleshooting below or ask a senior pirate.

---

Welcome, core team member! This guide covers everything you need for full development, debugging, and advanced workflows.

## 1. Project Setup
- Clone the repo
- Install dependencies (Python, Docker, Make, etc.)
- Set up environment variables
- Start all services:
  ```bash
  make -f Makefile.ai ai-up
  ```

## 1a. Starting Ollama Functions for Internal Testing
Some tests and internal workflows require the `test-ollama-functions` service (for LLM/embedding features). This service is **not started by default** with the main test environment.

To start it:
```bash
make -f Makefile.ai-test test-ollama-functions-up
```
To stop it:
```bash
make -f Makefile.ai-test test-ollama-functions-down
```
You only need to run this if you are working on features or tests that require Ollama/LLM functionality.

## 2. Dev Tools & Advanced Makefile Targets
- See all available targets:
  ```bash
  make -f Makefile.ai help
  # or review Makefile.ai directly
  ```
- Use advanced targets for migrations, testing, linting, and automation.
- How to add/extend targets:
  - Copy/paste an existing target as a template
  - Document new targets with comments
  - Use variables for flexibility (e.g., API_HOST)

## 3. Debugging & Migrations
- How to run and debug migrations
- How to use logs and troubleshooting targets
- How to reset or recover the database

## 4. Deep Dives
- For advanced/experimental topics, see [Onboarding Adventures](ONBOARDING_ADVENTURES.md)

---

## Troubleshooting

- **Tests fail with database errors (e.g., relation does not exist):**
  - Make sure you ran the migrations: `make -f Makefile.ai ai-db-migrate` and `make -f Makefile.ai ai-memorydb-migrate`
  - Try resetting the environment: `make -f Makefile.ai ai-env-down` then `make -f Makefile.ai ai-env-up`
- **Docker containers won't start:**
  - Check Docker is running
  - Try `make -f Makefile.ai ai-env-down` then `make -f Makefile.ai ai-env-up`
- **Still stuck?**
  - Ask in the team chat or ping a senior dev. We've all been there, matey!

---

**See also:** [Universal Onboarding](ONBOARDING.md) | [External Onboarding](ONBOARDING_EXTERNAL.md)

## Quickstart Targets: Dev vs Test

There are now two quickstart flows for different needs:

| Target            | What it does                                              | When to use                |
|-------------------|----------------------------------------------------------|----------------------------|
| `dev-quickstart`  | Sets up dev env, runs dev DB migrations, onboard admin, runs tests | For local development      |
| `test-quickstart` | Sets up test env, runs test DB migrations, runs tests (no onboarding) | For CI, test cycles, or when you want a clean test run |

### Example Usage

- **Local dev setup:**
  ```bash
  make -f Makefile.ai dev-db-nuke
  # or, if you just want to quickstart without nuking:
  make -f Makefile.ai dev-quickstart
  ```
- **Test/CI setup:**
  ```bash
  make -f Makefile.ai test-db-nuke
  # or, for a quick test run:
  make -f Makefile.ai test-quickstart
  ```

**Tip:** Use the right quickstart for your voyage! Dev for local hacking, test for clean test runs or CI. 
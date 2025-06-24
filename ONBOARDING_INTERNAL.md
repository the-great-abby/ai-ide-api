# Internal Developer Onboarding

## 🏴‍☠️ Quickstart (For New Crew)

Welcome aboard, matey! Follow these two steps to get your development environment shipshape and start your first adventure.

### Step 1: Set Up Your Development Environment

This command will prepare all the necessary services, databases, and configurations. It's your go-to command for a fresh start.

   ```bash
   make -f Makefile.ai quickstart
   ```

This process might take a few minutes. If you see green, you're ready for the next step! If not, see the Troubleshooting section below.

### Step 2: Begin Your Interactive Onboarding

Now that your environment is ready, it's time to begin your guided tour. This interactive script will introduce you to the key concepts and workflows.

```bash
make -f Makefile.ai onboard
```

Follow the prompts from your chosen crewmate to complete your first quest!

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
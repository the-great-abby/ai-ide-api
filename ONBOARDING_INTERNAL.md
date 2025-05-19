# Internal Developer Onboarding

Welcome, core team member! This guide covers everything you need for full development, debugging, and advanced workflows.

## 1. Project Setup
- Clone the repo
- Install dependencies (Python, Docker, Make, etc.)
- Set up environment variables
- Start all services:
  ```bash
  make -f Makefile.ai ai-up
  ```

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

**See also:** [Universal Onboarding](ONBOARDING.md) | [External Onboarding](ONBOARDING_EXTERNAL.md) 
# External/Partner Onboarding

Welcome, external collaborator or partner! This guide will help you get started quickly and use the project's essential features.

## 1. Quick Start
- Clone the repo
- Install dependencies (Python, Docker, Make, etc.)
- Start the main services:
  ```bash
  make -f Makefile.ai ai-up
  ```

## 2. Essential Makefile Targets
- List rules:
  ```bash
  make -f Makefile.ai ai-list-rules
  ```
- List enhancements:
  ```bash
  make -f Makefile.ai ai-list-enhancements
  ```
- Propose a rule or enhancement (see Makefile.ai for details)

## 3. How to Use/Extend Makefile Targets
- To add your own target, copy an existing one in `Makefile.ai` and modify as needed.
- Override variables (e.g., API_HOST) when running a target:
  ```bash
  make -f Makefile.ai ai-list-enhancements API_HOST=host.docker.internal
  ```
- Document your targets with comments for clarity.

## 4. Getting Help
- Use the `make help` target (if available) or review `Makefile.ai` for available commands.
- Reach out via the project's support channel or issue tracker if you get stuck.

## 5. Advanced/Experimental Topics
- See [Onboarding Adventures](ONBOARDING_ADVENTURES.md) for more advanced workflows and integrations.

---

**See also:** [Universal Onboarding](ONBOARDING.md) | [Internal Onboarding](ONBOARDING_INTERNAL.md) 
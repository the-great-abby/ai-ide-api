# Onboarding User Stories: LLM/Ollama Integration

## Overview
This document provides onboarding-focused user stories and actionable suggestions to help new users quickly and easily set up and use the AI-IDE's LLM (Ollama) integration. The goal is to ensure a smooth first-run experience and clear discoverability of all AI-powered features.

---

## User Story 1: Clear Getting Started Guide for LLM Features

**As a new AI-IDE user, I want a clear, step-by-step "Getting Started with LLM" guide, so I can quickly set up and use AI-powered features without confusion.**

**Acceptance Criteria:**
- There is a dedicated section in the README or onboarding docs titled "Getting Started with LLM/AI Features."
- The guide explains prerequisites (e.g., Docker, Make, Python version).
- The guide lists the exact Makefile commands to:
  - Download the LLM model
  - Start the Ollama service
  - Run the LLM-powered features (rule suggestion, code review, etc.)
- The guide explains how to verify the model/service is running (e.g., checking logs or a health endpoint).
- Troubleshooting tips are included for common issues (e.g., model not found, port conflicts).

---

## User Story 2: One-Command LLM Setup

**As a new user, I want a single Makefile target that sets up everything needed for LLM features, so I don't have to remember multiple commands.**

**Acceptance Criteria:**
- There is a Makefile target (e.g., `ai-llm-setup`) that:
  - Downloads the default model (if not present)
  - Starts the Ollama service
  - Verifies the service is running
- The command outputs clear next steps or confirmation of success.
- If any step fails, the output explains what went wrong and how to fix it.

---

## User Story 3: Guided First LLM-Driven Task

**As a new user, I want a guided example of running an LLM-powered feature (like rule suggestion), so I can see the value and workflow immediately.**

**Acceptance Criteria:**
- The onboarding docs include a "Your First LLM Task" section.
- The section walks the user through:
  - Running the setup command
  - Running a rule suggestion on a sample directory or file
  - Viewing the output and understanding what happened
- Screenshots or example outputs are provided.

---

## User Story 4: Discoverability of LLM-Related Makefile Targets

**As a new user, I want to easily discover all Makefile targets related to LLM/Ollama, so I know what's available and what each does.**

**Acceptance Criteria:**
- The README or a `make help` target lists and describes all LLM/Ollama-related Makefile targets.
- Each target has a short, clear description (e.g., "ai-ollama-pull-model: Download the default Ollama LLM model").
- There is a section in the docs or Makefile comments grouping these targets together.

---

## User Story 5: Environment and Model Configuration Guidance

**As a new user, I want clear instructions on how to change the LLM model or endpoint, so I can customize my environment if needed.**

**Acceptance Criteria:**
- The onboarding docs explain how to override the default model (e.g., `make -f Makefile.ai ai-ollama-pull-model OLLAMA_MODEL=my-model:latest`).
- The docs explain how to set environment variables for custom endpoints or ports.
- There are examples for both local and Dockerized workflows.

---

## User Story 6: Troubleshooting and FAQ for LLM Integration

**As a new user, I want a troubleshooting/FAQ section for LLM features, so I can quickly resolve common setup and usage issues.**

**Acceptance Criteria:**
- The docs include a "Troubleshooting LLM Integration" section.
- Common issues (model not found, Docker errors, port conflicts, service not starting) are listed with solutions.
- There are links to relevant logs or diagnostic commands (e.g., `make -f Makefile.ai ai-ollama-logs`).

---

## Suggestions to Make Onboarding Easier

- **Add a `make help` or `make llm-help` target** that prints all LLM/Ollama-related commands and their descriptions.
- **Bundle a sample project or test directory** so users can try LLM features without needing to set up their own codebase first.
- **Provide a script or Makefile target** that checks for prerequisites (Docker, Make, Python) and warns if missing.
- **Add inline comments** in the Makefile for each LLM-related target, making it easier to understand for those browsing the file.
- **Link to Ollama documentation** for advanced users who want to customize models or endpoints.

---

Feel free to expand these stories or adapt them for your onboarding documentation, README, or internal wiki! 
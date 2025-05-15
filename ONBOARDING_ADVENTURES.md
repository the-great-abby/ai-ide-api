# 🧭 Onboarding Adventures: User Stories as Breadcrumbs

Welcome to your first week in the AI IDE System! This guide uses user stories as breadcrumbs to help you discover, learn, and master the platform. Follow these adventures to become productive and confident in your workflow.

---

## Day 1: Getting Set Up
**User Story:**  
As a new developer, I want to set up my environment so I can run the project locally and access all core services.

**Breadcrumbs:**
- Clone the repository.
- Run `make -f Makefile.ai ai-up` to start the core services.
- Visit the admin frontend at [http://localhost:3000](http://localhost:3000).
- Run `make -f Makefile.ai ai-status` to check service health.

---

## Day 2: Running and Understanding Tests
**User Story:**  
As a developer, I want to run all tests using Makefile.ai so I follow best practices and catch issues early.

**Breadcrumbs:**
- Run `make -f Makefile.ai ai-test-unit PYTEST_ARGS="-x"` for unit tests.
- Run `make -f Makefile.ai ai-test-integration PYTEST_ARGS="-x"` for integration tests.
- Read the test results and learn about the test network setup.

---

## Day 3: Exploring Rules and Proposals
**User Story:**  
As a contributor, I want to propose a new rule via the API so my ideas are reviewed and tracked.

**Breadcrumbs:**
- Visit the "Rules" section in the admin frontend.
- Use the API endpoint `/propose-rule-change` to submit a new rule.
- Review pending proposals in the UI or with `make -f Makefile.ai ai-list-pending`.
- Approve or reject proposals as an admin.

---

## Day 4: Database Safety and Backups
**User Story:**  
As a maintainer, I want to back up the database before destructive changes so I can recover if needed.

**Breadcrumbs:**
- Run `make -f Makefile.ai ai-db-backup` for a full backup.
- Run `make -f Makefile.ai ai-db-backup-data-only` for a data-only backup.
- Restore from backup with `make -f Makefile.ai ai-db-restore BACKUP=...`.

---

## Day 5: Automating Documentation with AI
**User Story:**  
As a maintainer, I want to use AI to generate user stories for rules and enhancements so documentation stays up to date.

**Breadcrumbs:**
- Run `make -f Makefile.ai ai-misc-update-missing-user-stories` to auto-generate user stories for rules.
- Review and edit generated user stories in the admin frontend.
- Repeat for enhancements and proposals.

---

## Day 6: Discovering Advanced Features
**User Story:**  
As a power user, I want to explore advanced Makefile targets and API endpoints to automate my workflow.

**Breadcrumbs:**
- List all Makefile targets with `cat Makefile.ai | grep ':'`.
- Explore `/docs` for API documentation.
- Try batch proposing rules or running the LLM-powered rule suggestion pipeline.

---

## Day 7: Contributing and Leveling Up
**User Story:**  
As a team member, I want to contribute new user stories, rules, and enhancements to help others on their journey.

**Breadcrumbs:**
- Add new user stories as `.mdc` files in `.cursor/rules/`.
- Propose improvements to onboarding or documentation.
- Share feedback and ideas in team meetings or via the feedback API.

---

# 🗺️ User Journey Map (Visual Outline)

1. **Start Here:**  
   Environment setup → Service health check → First login

2. **Core Workflows:**  
   Running tests → Reviewing rules → Proposing changes

3. **Safety & Recovery:**  
   Backups → Restores → Migration management

4. **Automation & AI:**  
   LLM-powered documentation → Batch updates → Smart suggestions

5. **Exploration & Mastery:**  
   Advanced Makefile/API usage → Custom scripts → Contributing new stories

---

## How to Use This Guide
- Follow each day's adventure to build confidence and mastery.
- Use the breadcrumbs as checklists or quick references.
- Add your own user stories and adventures as you discover new workflows! 
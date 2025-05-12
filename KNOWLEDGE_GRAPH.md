# Project Knowledge Graph

## Overview

This knowledge graph is auto-generated from the database.

```mermaid
graph TD
  API[API Backend]
  FE[Admin Frontend]
  DB[(Postgres DB)]
  RULES[Rules]
  ENH[Enhancements]
  TESTS[Tests]
  API --> DB
  FE --> API
  API --> RULES
  API --> ENH
  TESTS --> API
  RULES -->|applies to| API
  ENH -->|proposes| RULES
  RULE_510aede7-b47b-42a4-94ce-13a3914ce6c4["Rule: Projects must provid..."]
  RULES --> RULE_510aede7-b47b-42a4-94ce-13a3914ce6c4
  RULE_60ad6ecd-15f7-4b4b-8fcf-b3f63f20781a["Rule: All new rules must b..."]
  RULES --> RULE_60ad6ecd-15f7-4b4b-8fcf-b3f63f20781a
  ENH_403181e3-40cb-4fa1-a59a-85e54de27945["Enh: Add a project field ..."]
  ENH --> ENH_403181e3-40cb-4fa1-a59a-85e54de27945
  ENH_6ceefb3b-9c02-4489-a4b5-ca91fafb6b43["Enh: Maintain an up-to-da..."]
  ENH --> ENH_6ceefb3b-9c02-4489-a4b5-ca91fafb6b43
```

## Entities

- **API Backend:** FastAPI app, serves rules and proposals.
- **Admin Frontend:** React/Vite app for admin tasks.
- **Rules:** Stored in DB, managed via API.
- **Enhancements:** Suggestions for new rules or features.
- **Tests:** Pytest suite, run via Makefile.ai.

## Workflows

1. **Propose Rule:**  
   User → `/propose-rule-change` → API → DB

2. **Suggest Enhancement:**  
   User → `/suggest-enhancement` → API → DB

3. **Approve Rule:**  
   Admin → `/approve-rule-change/{id}` → API → DB

4. **Run Tests:**  
   `make -f Makefile.ai ai-test` → Docker → API → DB

## References

- [ONBOARDING.md](./ONBOARDING.md)
- [RULES.md](./RULES.md)

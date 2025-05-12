import os
import psycopg2

DB_NAME = os.environ.get("POSTGRES_DB", "rulesdb")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.environ.get("POSTGRES_HOST", "db-test")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

cur.execute("SELECT id, description, project FROM rules;")
rules = cur.fetchall()

cur.execute("SELECT id, description, project, status FROM enhancements;")
enhancements = cur.fetchall()

mermaid = [
    "graph TD",
    "  API[API Backend]",
    "  FE[Admin Frontend]",
    "  DB[(Postgres DB)]",
    "  RULES[Rules]",
    "  ENH[Enhancements]",
    "  TESTS[Tests]",
    "  API --> DB",
    "  FE --> API",
    "  API --> RULES",
    "  API --> ENH",
    "  TESTS --> API",
    "  RULES -->|applies to| API",
    "  ENH -->|proposes| RULES"
]

for rule in rules:
    label = f'Rule: {rule[1][:20]}...' if rule[1] else f'Rule: {rule[0]}'
    mermaid.append(f'  RULE_{rule[0]}[\"{label}\"]')
    mermaid.append(f'  RULES --> RULE_{rule[0]}')
for enh in enhancements:
    label = f'Enh: {enh[1][:20]}...' if enh[1] else f'Enh: {enh[0]}'
    mermaid.append(f'  ENH_{enh[0]}[\"{label}\"]')
    mermaid.append(f'  ENH --> ENH_{enh[0]}')

with open("KNOWLEDGE_GRAPH.md", "w") as f:
    f.write("# Project Knowledge Graph\n\n")
    f.write("## Overview\n\n")
    f.write("This knowledge graph is auto-generated from the database.\n\n")
    f.write("```mermaid\n")
    f.write("\n".join(mermaid))
    f.write("\n```\n\n")
    f.write("## Entities\n\n")
    f.write("- **API Backend:** FastAPI app, serves rules and proposals.\n")
    f.write("- **Admin Frontend:** React/Vite app for admin tasks.\n")
    f.write("- **Rules:** Stored in DB, managed via API.\n")
    f.write("- **Enhancements:** Suggestions for new rules or features.\n")
    f.write("- **Tests:** Pytest suite, run via Makefile.ai.\n\n")
    f.write("## Workflows\n\n")
    f.write("1. **Propose Rule:**  \n   User → `/propose-rule-change` → API → DB\n\n")
    f.write("2. **Suggest Enhancement:**  \n   User → `/suggest-enhancement` → API → DB\n\n")
    f.write("3. **Approve Rule:**  \n   Admin → `/approve-rule-change/{id}` → API → DB\n\n")
    f.write("4. **Run Tests:**  \n   `make -f Makefile.ai ai-test` → Docker → API → DB\n\n")
    f.write("## References\n\n")
    f.write("- [ONBOARDING.md](./ONBOARDING.md)\n")
    f.write("- [RULES.md](./RULES.md)\n")

cur.close()
conn.close() 
# Changelog

## [Unreleased]

### 🚀 Migrated from SQLite to Postgres (Dockerized)

- **Database backend upgraded:**
  The project's data layer has been migrated from a local SQLite database (`rules.db`) to a robust, containerized Postgres instance (`rules-postgres`).
- **Fully automated migration:**
  - All tables and data are now migrated using a repeatable, Docker-based process.
  - Makefile.ai targets (`ai-migrate-sqlite-to-postgres-csv`) and a shell script (`import_csvs.sh`) ensure smooth, cross-platform migrations.
  - Handles schema conversion, data import, and empty tables gracefully.
- **Benefits:**
  - Improved scalability and reliability for production and development.
  - Easier integration with other services and cloud platforms.
  - Consistent, versioned database setup for all contributors and CI.
- **How to use:**
  - See the Makefile.ai for migration and database management commands.
  - All app services now connect to Postgres by default.

### ✨ Enhancements

- **Project-specific tracking:** Added a `project` field to rule and enhancement submissions, enabling project-specific rule/enhancement management and filtering.
- **Automated knowledge graph:** Implemented an automated, database-driven knowledge graph (`KNOWLEDGE_GRAPH.md`) with a Makefile target (`make generate-knowledge-graph`) for easy updates and onboarding. 
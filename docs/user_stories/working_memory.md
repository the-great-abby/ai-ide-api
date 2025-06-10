# User Story: Working Memory (Graph + Vector)

## Motivation
As a developer or AI agent, I want to store, relate, and search memory nodes so that I (and the AI) can recall relevant information, discover connections, and explain reasoning. This enables richer context, better recommendations, and explainable AI behavior.

## Actors
- Developers
- AI agents
- Automation scripts

## Preconditions
- API and memorydb are running
- User has a valid API token with appropriate permissions
- Memory endpoints are enabled and accessible

## Step-by-Step Actions
1. **Create a memory node**
   - POST to `/memory/nodes` with content, namespace, and optional meta
2. **List memory nodes**
   - GET `/memory/nodes?namespace=...` to verify node presence
3. **Create a second node and relate them**
   - POST to `/memory/nodes` for the second node
   - POST to `/memory/edges` to create an edge (e.g., `related_to`)
4. **List edges and verify the relationship**
   - GET `/memory/edges?from_id=...&to_id=...`
5. **Perform a vector search for similar nodes**
   - (If supported) Use the vector search endpoint or semantic search feature
6. **Traverse the graph from a node**
   - (If supported) Use graph traversal endpoints or list edges by relation
7. **Delete nodes and verify cleanup**
   - DELETE `/memory/nodes?namespace=...`
   - GET `/memory/nodes?namespace=...` to confirm deletion

## Expected Outcomes
- Memory nodes and edges are persistent and queryable
- Semantic (vector) and relational (graph) queries both work
- Permissions are enforced for all operations
- The system supports both AI and human workflows

## Best Practices
- Use namespaces for isolation and organization
- Clean up test data after tests or demos
- Use meta fields for rich context and searchability
- Document memory operations in user stories and onboarding
- Regularly run integration tests to catch regressions

## References
- End-to-end test: `tests/integration/test_memory_endpoints.py`
- Memory endpoints: `/memory/nodes`, `/memory/edges`
- Memory system guide: `docs/onboarding/MEMORY_SYSTEM.md`
- Makefile targets: `Makefile.ai-memory`

## Database Extension Requirements

This application requires the following PostgreSQL extensions to be installed in both `rulesdb` and `memorydb`:

- `pgvector`: Enables vector search and storage of embeddings for semantic memory and similarity queries.
- `pg_trgm`: Enables fuzzy string matching and similarity search for text fields, allowing typo-tolerant and partial matches.

### What is `pg_trgm`?

`pg_trgm` is a PostgreSQL extension that provides trigram-based text search and similarity operators. It allows the app to find and rank similar strings, even with typos or partial matches, making search and autocomplete more robust.

**Both extensions are installed automatically as part of the database initialization process.**

## Manual Fallback for Extensions

If you ever nuke the database and find that `pg_trgm` (or any required extension) is missing, you can install it manually with these commands:

```bash
docker compose -f docker-compose.test.yml exec test-db psql -U postgres -d rulesdb -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm;'
docker compose -f docker-compose.test.yml exec test-db psql -U postgres -d memorydb -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm;'
```

This should only be needed if the automated process fails. If you see errors about missing operators or fuzzy search, run these commands to patch your DBs and get back to smooth sailing! 
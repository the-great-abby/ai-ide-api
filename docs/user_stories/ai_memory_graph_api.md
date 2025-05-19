# User Story: AI Memory Graph API for Storing and Relating Ideas

## Table of Contents
1. [Motivation](#motivation)
2. [Actors](#actors)
3. [Preconditions](#preconditions)
4. [Recommended Automation: Docker Scripts & Makefile Targets](#recommended-automation-docker-scripts--makefile-targets)
5. [Step-by-Step Actions](#step-by-step-actions)
    - [1. Add a memory node (idea/note)](#1-add-a-memory-node-ideanote)
    - [2. List all memory nodes](#2-list-all-memory-nodes)
    - [3. Add a relationship (edge) between nodes](#3-add-a-relationship-edge-between-nodes)
    - [4. List all edges](#4-list-all-edges)
    - [5. Search for similar nodes by embedding or text](#5-search-for-similar-nodes-by-embedding-or-text)
    - [6. Traverse the memory graph](#6-traverse-the-memory-graph)
    - [7. Delete memory nodes by namespace](#7-delete-memory-nodes-by-namespace)
6. [Expected Outcomes](#expected-outcomes)
7. [Best Practices](#best-practices)
8. [Example curl Commands](#example-curl-commands)
9. [References](#references)
10. [CI Testing and Script-Based Integration Tests](#ci-testing-and-script-based-integration-tests)

## Important Note (2025-05-18)
> The 'embedding' field is now always generated server-side for memory nodes. Do NOT provide 'embedding' in POST /memory/nodes requests or in test fixtures. The backend will generate and return the embedding automatically. The embedding dimension is now 768 floats (matching the current model).

## Motivation
As an AI system or developer, I want to store, relate, and search ideas, notes, and thoughts in a memory graph, so that the AI can build, traverse, and retrieve knowledge efficiently using both semantic similarity and explicit relationships.

## Actors
- AI system
- Developer
- Knowledge engineer

## Preconditions
- The FastAPI server is running and accessible (default: http://localhost:9103)
- The memory graph API endpoints are enabled
- The embedding dimension matches the model used (e.g., 1536 floats)

## Recommended Automation: Docker Scripts & Makefile Targets

For onboarding, automation, and reproducibility, it is recommended to use the provided Dockerized utility scripts and Makefile.ai targets for all memory graph operations. These scripts allow you to add nodes/edges, list, traverse, filter, and export the memory graph without installing dependencies on your host.

- **Build the utility image:**
  ```bash
  make -f Makefile.ai ai-memory-utils-build
  ```
- **Run operations via Makefile targets:**
  ```bash
  make -f Makefile.ai ai-memory-add-node NAMESPACE=notes CONTENT="My note" META='{"tags":["example"]}'
  make -f Makefile.ai ai-memory-list-nodes
  make -f Makefile.ai ai-memory-traverse-multi-hop NODE_ID=<your_node_id>
  # ...and more (see ONBOARDING_OTHER_AI_IDE.md for full list)
  ```
- **See [`ONBOARDING_OTHER_AI_IDE.md`](../ONBOARDING_OTHER_AI_IDE.md) for a complete list of targets and usage examples.**

This approach is recommended for onboarding new AI IDEs, running batch operations, and ensuring consistency across environments.

## Step-by-Step Actions

### 1. Add a memory node (idea/note)
Send a POST request to `/memory/nodes` with the content and optional metadata. Do NOT include 'embedding' in the request body or in test code; it will be generated server-side.

### 2. List all memory nodes
Send a GET request to `/memory/nodes` to retrieve all stored nodes.

### 3. Add a relationship (edge) between nodes
Send a POST request to `/memory/edges` with the IDs of the nodes and the relationship type.

### 4. List all edges
Send a GET request to `/memory/edges` to retrieve all relationships.

### 5. Search for similar nodes by embedding or text
You can now search for similar nodes by providing either:
- `text`: The server will generate the embedding from your text and use it for the search (preferred for most users).
- `embedding`: (Advanced) Provide your own embedding vector for the search.

Send a POST request to `/memory/nodes/search` with either a `text` or `embedding` field, plus optional `namespace` and `limit`.

**Example: Search by text (preferred)**
```bash
curl -X POST http://localhost:9103/memory/nodes/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Find similar ideas about AI memory.",
    "namespace": "notes",
    "limit": 5
  }'
```

**Example: Search by embedding (advanced)**
```bash
curl -X POST http://localhost:9103/memory/nodes/search \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    "namespace": "notes",
    "limit": 5
  }'
```

### 6. Traverse the memory graph
To move from one memory node to related nodes, follow the edges (relationships) in the graph. You can traverse forward (from a node to others it points to), backward (to nodes that point to it), or filter by relation type.

**Step-by-step:**
1. **List outgoing edges from a node:**
   - `GET /memory/edges?from_id=NODE_ID`
2. **List incoming edges to a node:**
   - `GET /memory/edges?to_id=NODE_ID`
3. **Filter by relation type:**
   - `GET /memory/edges?from_id=NODE_ID&relation_type=TYPE`
4. **Fetch connected nodes:**
   - For each edge, use the `to_id` (or `from_id` for incoming) to fetch the connected node from `/memory/nodes`.
5. **Repeat as needed:**
   - Continue traversing by following edges from each new node.

**Example traversal flow:**
- Start with a node's `id` (e.g., `abc-123`).
- List all outgoing edges: `curl "http://localhost:9103/memory/edges?from_id=abc-123" | jq .`
- For each edge, note the `to_id` and fetch that node: `curl "http://localhost:9103/memory/nodes" | jq '.[] | select(.id == "THE_TO_ID")'`
- Repeat to walk the graph.

### 7. Delete memory nodes by namespace
To clean up or reset a namespace, you can delete all memory nodes in that namespace (or all nodes if no namespace is provided).

**API:**
```http
DELETE /memory/nodes?namespace=YOUR_NAMESPACE
```

**Example curl:**
```bash
curl -X DELETE "http://localhost:9103/memory/nodes?namespace=testns"
```

**Delete all nodes:**
```bash
curl -X DELETE "http://localhost:9103/memory/nodes"
```

**Makefile usage:**
```bash
make -f Makefile.ai ai-memory-delete-nodes NAMESPACE=testns
```

**Best Practices:**
- Use a unique namespace per test run for isolation.
- Clean up test data after tests to avoid collisions.
- Use this endpoint for onboarding, migration, and disaster recovery workflows.
- For most use cases, prefer searching by `text` and let the server generate the embedding.
- Only use the `embedding` field if you have a precomputed embedding or advanced workflow.

## Expected Outcomes
- Ideas/notes are stored as nodes with embeddings and metadata.
- Relationships between ideas are stored as edges.
- The AI can retrieve similar ideas using vector search.
- The AI can traverse and analyze relationships between ideas.

## Best Practices
- Use consistent namespaces to organize different types of memories.
- Store relevant metadata (tags, user, etc.) as JSON in the metadata field.
- Use meaningful relation types (e.g., "inspired_by", "contradicts").
- Ensure embeddings are generated with the same model/dimension (currently 768 floats).
- Regularly back up the memorydb database.
- **Prefer the provided Makefile.ai targets and Dockerized scripts for onboarding, automation, and reproducibility.**
- **For traversal:**
  - Use forward traversal (`from_id`) to find what a node points to.
  - Use backward traversal (`to_id`) to find what points to a node.
  - Filter by `relation_type` to follow only certain relationships.
  - Avoid circular traversals unless intentionally analyzing cycles.
  - Automate traversal with scripts for complex queries.

## Example curl Commands

### Add a memory node
```bash
curl -X POST http://localhost:9103/memory/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "notes",
    "content": "This is an idea about AI memory.",
    "meta": "{\"tags\": [\"ai\", \"memory\"]}"
  }'
```

### List all memory nodes
```bash
curl http://localhost:9103/memory/nodes
```

### Add a relationship (edge)
```bash
curl -X POST http://localhost:9103/memory/edges \
  -H "Content-Type: application/json" \
  -d '{
    "from_id": "UUID-OF-NODE-1",
    "to_id": "UUID-OF-NODE-2",
    "relation_type": "inspired_by",
    "metadata": "{\"note\": \"A inspired B\"}"
  }'
```

### List all edges
```bash
curl http://localhost:9103/memory/edges
```

### Search for similar nodes
```bash
curl -X POST http://localhost:9103/memory/nodes/search \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    "namespace": "notes",
    "limit": 5
  }'
```

### Traverse the memory graph (list edges from a node)
```bash
curl "http://localhost:9103/memory/edges?from_id=NODE_ID"
```

### Traverse the memory graph (list edges to a node)
```bash
curl "http://localhost:9103/memory/edges?to_id=NODE_ID"
```

### Fetch a connected node by ID
```bash
curl http://localhost:9103/memory/nodes | jq '.[] | select(.id == "THE_TO_ID")'
```

### Traverse and fetch all directly connected nodes (example bash loop)
```bash
for to_id in $(curl -s "http://localhost:9103/memory/edges?from_id=NODE_ID" | jq -r '.[].to_id'); do
  curl -s http://localhost:9103/memory/nodes | jq --arg id "$to_id" '.[] | select(.id == $id)'
done
```

## References
- [rule_api_server.py](../rule_api_server.py)
- [db.py](../db.py)

## CI Testing and Script-Based Integration Tests

Script-based memory graph tests (using the Dockerized utility scripts and Makefile targets) are available for full end-to-end coverage. These tests:
- Exercise the onboarding and automation flows as a real user or AI IDE would.
- Can be enabled in CI by setting the environment variable `RUN_DOCKER_SCRIPT_TESTS=1`.
- Are **optional** for most workflows, but recommended for:
  - Validating onboarding and automation
  - Ensuring scripts remain in sync with the API
  - Detecting breakage in Docker/Makefile-based flows

**Best Practices:**
- Run these tests locally before major releases or onboarding changes.
- Enable in CI for full coverage if Docker-in-Docker is supported and test time is not a concern.
- Keep these tests marked as 'slow' or 'optional' in CI to avoid blocking fast feedback cycles.

**Future Plans:**
- Consider enabling script-based tests in CI as the project matures or for release candidates.
- Document any CI configuration changes in ONBOARDING.md and ONBOARDING_OTHER_AI_IDE.md.

--- 
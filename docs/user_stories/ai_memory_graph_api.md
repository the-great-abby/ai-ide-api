# User Story: AI Memory Graph API for Storing and Relating Ideas

## Table of Contents
1. [Motivation](#motivation)
2. [Actors](#actors)
3. [Preconditions](#preconditions)
4. [Step-by-Step Actions](#step-by-step-actions)
    - [1. Add a memory node (idea/note)](#1-add-a-memory-node-ideanote)
    - [2. List all memory nodes](#2-list-all-memory-nodes)
    - [3. Add a relationship (edge) between nodes](#3-add-a-relationship-edge-between-nodes)
    - [4. List all edges](#4-list-all-edges)
    - [5. Search for similar nodes by embedding](#5-search-for-similar-nodes-by-embedding)
    - [6. Traverse the memory graph](#6-traverse-the-memory-graph)
5. [Expected Outcomes](#expected-outcomes)
6. [Best Practices](#best-practices)
7. [Example curl Commands](#example-curl-commands)
8. [References](#references)

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

## Step-by-Step Actions

### 1. Add a memory node (idea/note)
Send a POST request to `/memory/nodes` with the content, embedding, and optional metadata.

### 2. List all memory nodes
Send a GET request to `/memory/nodes` to retrieve all stored nodes.

### 3. Add a relationship (edge) between nodes
Send a POST request to `/memory/edges` with the IDs of the nodes and the relationship type.

### 4. List all edges
Send a GET request to `/memory/edges` to retrieve all relationships.

### 5. Search for similar nodes by embedding
Send a POST request to `/memory/nodes/search` with a query embedding and optional namespace/limit.

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

## Expected Outcomes
- Ideas/notes are stored as nodes with embeddings and metadata.
- Relationships between ideas are stored as edges.
- The AI can retrieve similar ideas using vector search.
- The AI can traverse and analyze relationships between ideas.

## Best Practices
- Use consistent namespaces to organize different types of memories.
- Store relevant metadata (tags, user, etc.) as JSON in the metadata field.
- Use meaningful relation types (e.g., "inspired_by", "contradicts").
- Ensure embeddings are generated with the same model/dimension.
- Regularly back up the memorydb database.
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
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    "metadata": "{\"tags\": [\"ai\", \"memory\"]}"
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
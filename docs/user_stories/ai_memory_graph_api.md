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

## References
- [rule_api_server.py](../rule_api_server.py)
- [db.py](../db.py) 
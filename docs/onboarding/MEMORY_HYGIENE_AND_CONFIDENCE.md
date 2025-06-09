# Memory Hygiene, Time-Based Expiry, and Confidence Scoring Guide

This guide explains how to keep your memory system clean, relevant, and trustworthy by using timestamps, time-based expiry, and confidence scores. It's designed to help you avoid memory pollution and surface the most useful knowledge.

---

## 1. Why Memory Hygiene Matters
- Prevents the memory system from being cluttered with outdated or irrelevant information.
- Improves search quality and system performance.
- Builds trust in the AI's recommendations and context.

---

## 2. Adding Timestamps to Memory Entries
- **Schema Update:** Add `created_at` and (optionally) `updated_at` fields to each memory node/document. Use ISO 8601 timestamps.
- **Automatic Assignment:** Set `created_at` when the memory is first stored; update `updated_at` on changes.
- **Expiry/TTL:** Optionally, add a `ttl` (time-to-live) or `expires_at` field for auto-expiry.

**Example Schema:**
```json
{
  "id": "abc123",
  "content": "pytest must use Makefile.ai",
  "created_at": "2024-06-10T12:00:00Z",
  "updated_at": "2024-06-10T12:00:00Z",
  "expires_at": null,
  "status": "active"
}
```

---

## 3. Filtering and Searching by Date
- Allow queries to specify a date range (e.g., "memories from the last 30 days").
- Exclude expired or archived nodes from default search results.

**Example Query:**
```json
{
  "query": "pytest",
  "date_from": "2024-06-01T00:00:00Z",
  "date_to": "2024-06-10T23:59:59Z"
}
```

---

## 4. Adding and Using Confidence Scores
- **Vector Search:** Most vector search engines return a similarity score for each result (e.g., cosine similarity).
- **Score Normalization:** Normalize the score to a 0–1 or 0–100% range for easier interpretation.
- **Include in API Response:** Add a `confidence` or `relevance` field to each search result.
- **Display in UI/Logs:** Show the confidence score to users or in logs to help interpret results.

**Example API Response:**
```json
{
  "id": "abc123",
  "content": "pytest must use Makefile.ai",
  "created_at": "2024-06-10T12:00:00Z",
  "confidence": 0.92
}
```

---

## 5. Best Practices for Pruning and Surfacing Relevant Knowledge
- Use status fields (`active`, `archived`, `superseded`) to filter out irrelevant nodes.
- Schedule regular cleanups to archive or delete old/unused data.
- Use recency, status, and confidence to rank search results.
- Allow users and AI to flag irrelevant or outdated information.

---

## 6. Example: Memory Node Schema
```json
{
  "id": "123",
  "type": "rule",
  "content": "...",
  "status": "active",
  "created_at": "2024-06-01T12:00:00Z",
  "updated_at": "2024-06-10T09:00:00Z",
  "expires_at": null,
  "confidence": 0.87,
  "tags": ["pytest", "testing"],
  "supersedes": "122",
  "superseded_by": null
}
```

---

## 7. How to Update Your Codebase
- Update your memory node schema to include timestamps and confidence fields.
- Update API endpoints to accept date filters and return confidence scores.
- Add scheduled jobs or scripts for pruning/archiving old data.
- Document your memory hygiene policy and share it with your team.

---

## 8. Further Reading
- See the [Memory System Guide](MEMORY_SYSTEM.md) for an overview of the memory architecture.
- Research vector search engines (pgvector, Pinecone, FAISS) for confidence scoring.

---

*See something missing? Please add your tips or examples!* 
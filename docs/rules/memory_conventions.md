# 🧠 Memory System Conventions: Namespaces & Tags

## Why Conventions Matter
- **Searchability:** Consistent namespaces and tags make it easy to find relevant memories.
- **Organization:** Prevents memory pollution and keeps related data grouped.
- **Collaboration:** Crew can quickly understand and use shared memory nodes.

---

## Namespace Conventions
Namespaces are required and should be descriptive. Use these patterns:

- **By File:**
  - `file:api/onboarding_endpoints.py`
  - `file:worker/memory_worker.py`
- **By Feature:**
  - `feature:memory-system`
  - `feature:api-auth`
- **By User:**
  - `user:abby`
  - `user:external-123`
- **By Session/Date:**
  - `session:2024-06-10-xyz`
  - `date:2024-06-10`
- **By Project/Component:**
  - `project:ai-ide-api`
  - `component:frontend`

**Tips:**
- Use lowercase and dashes/underscores for readability.
- Be as specific as needed, but avoid overly long namespaces.
- Combine patterns if helpful: `file:api/onboarding_endpoints.py|feature:external-onboarding`

---

## Tagging Best Practices
Tags are for quick filtering and grouping. Use them to add context, status, or type.

- **Purpose:**
  - Mark type: `bug`, `docs`, `example`, `test`, `api`
  - Mark status: `urgent`, `reviewed`, `archived`
  - Mark audience: `internal`, `external`, `admin`
- **Examples:**
  - `"tags": ["api", "external", "example"]`
  - `"tags": ["bug", "urgent"]`
- **Multi-tagging:**
  - Use as many tags as needed, but keep them relevant.

**Tips:**
- Use single words, lowercase.
- Avoid redundant tags (e.g., both `api` and `endpoint` if they mean the same thing).
- Add new tags as the project evolves, but document them.

---

## About 'score'
- **Score** is typically handled by the system (e.g., for search ranking or relevance).
- **Do not pass 'score'** in your API payloads unless explicitly instructed—let the system calculate and update it.

---

## Memory Workers: Current State
- **Automated memory workers** for updating, cleaning, or scoring memories are **planned** but not yet fully implemented.
- For now, memory updates and cleanup are manual or triggered by user/API actions.
- Stay tuned for future updates as memory workers come online!

---

## Example API Payloads

**Add a memory node (by file, with tags):**
```json
{
  "namespace": "file:api/onboarding_endpoints.py",
  "content": "Documented the onboarding endpoint for external use.",
  "meta": "{\"tags\":[\"docs\",\"api\"],\"file\":\"api/onboarding_endpoints.py\",\"author\":\"abby\"}"
}
```

**Add a memory node (by feature, with status):**
```json
{
  "namespace": "feature:memory-system",
  "content": "Added support for namespace conventions.",
  "meta": "{\"tags\":[\"feature\",\"reviewed\"]}"
}
```

---

## Tips for Clean & Useful Memory Data
- Always use a namespace and at least one tag.
- Include file, function, or author in meta for traceability.
- Review and clean up outdated or irrelevant nodes regularly.
- Use edges to relate nodes, but avoid over-linking.
- Document new tags and namespace patterns as they emerge.

---

**For questions or to propose new conventions, contact the memory system maintainers or open a discussion in the docs!** 
# External Project Memory API Onboarding

## Overview
You can use the AI IDE API as a hosted memory (vector) server for your own project—no direct DB or Docker access required.

## Prerequisites
- API key (ask your admin or use the onboarding/init endpoint)
- Project/namespace name
- API base URL (e.g., https://your-ai-ide-api.example.com)

## Quickstart

1. **Get Your API Key**
   - Contact your admin or use the `/onboarding/init` endpoint to obtain an API key.

2. **Create a Namespace**
   - Decide on a unique namespace for your project (e.g., your-project-name).

3. **Store a Memory Node**
   ```python
   import requests
   API_URL = "https://your-ai-ide-api.example.com"
   API_KEY = "your_api_key_here"
   headers = {"Authorization": f"Bearer {API_KEY}"}
   node = {"namespace": "my_project", "content": "Hello, memory!"}
   resp = requests.post(f"{API_URL}/memory/nodes", json=node, headers=headers)
   print(resp.json())
   ```

4. **Search Memory**
   ```python
   search = {"namespace": "my_project", "query": "Hello"}
   resp = requests.post(f"{API_URL}/memory/search", json=search, headers=headers)
   print(resp.json())
   ```

5. **Review API Docs**
   - Visit `/docs` on your API host for the full OpenAPI reference and example requests.

## Resources
- [Python Quickstart Script](/onboarding/scripts/memory_quickstart.py)
- [Postman Collection](/onboarding/scripts/memory_api.postman_collection.json)

## Troubleshooting
- **401 Unauthorized:** Check your API key.
- **404 Namespace not found:** Make sure you've created your project/namespace.
- **422 Validation error:** Check your request body for required fields.

## Advanced
- See the full API reference for batch operations, metadata, and more.
- For automation, you can script onboarding by calling `/onboarding/init` and then using the memory endpoints.

---

For questions or help, contact your AI IDE API administrator or see the [main documentation](/docs). 
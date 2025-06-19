# External Project Memory API Onboarding

## Overview
You can use the AI IDE API as a hosted memory (vector) server for your own project—no direct DB or Docker access required.

## Prerequisites
- API key (ask your admin or use the onboarding/init endpoint)
- Project/namespace name
- API base URL (e.g., https://your-ai-ide-api.example.com)
- **LLM access** (for AI-powered features like semantic search)

## Quickstart

### Option 1: Automated Onboarding (Recommended)
```bash
# Download and run the onboarding script
curl -O https://your-ai-ide-api.example.com/onboarding/scripts/onboard_external.sh
chmod +x onboard_external.sh
./onboard_external.sh
```

The script will:
- ✅ Initialize your project and team
- ✅ Generate API tokens with proper permissions
- ✅ Enable LLM access (if admin token is generated)
- ✅ Test the memory API functionality
- ✅ Create configuration files

### Option 2: Manual Setup

1. **Get Your API Key**
   - Contact your admin or use the `/onboarding/init` endpoint to obtain an API key.

2. **Enable LLM Access** (Required for AI features)
   ```bash
   # If you have an admin token, enable LLM access
   curl -X POST "https://your-ai-ide-api.example.com/memory/admin/project/llm-access" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "project_id": "YOUR_PROJECT_ID",
       "has_llm_access": true
     }'
   ```

3. **Create a Namespace**
   - Decide on a unique namespace for your project (e.g., your-project-name).

4. **Store a Memory Node**
   ```python
   import requests
   API_URL = "https://your-ai-ide-api.example.com"
   API_KEY = "your_api_key_here"
   headers = {"Authorization": f"Bearer {API_KEY}"}
   node = {"namespace": "my_project", "content": "Hello, memory!"}
   resp = requests.post(f"{API_URL}/memory/nodes", json=node, headers=headers)
   print(resp.json())
   ```

5. **Search Memory** (Requires LLM access for semantic search)
   ```python
   search = {"namespace": "my_project", "query": "Hello"}
   resp = requests.post(f"{API_URL}/memory/search", json=search, headers=headers)
   print(resp.json())
   ```

6. **Review API Docs**
   - Visit `/docs` on your API host for the full OpenAPI reference and example requests.

## 🤖 LLM Access

### What is LLM Access?
LLM access enables AI-powered features:
- **Semantic Search**: Find memories by meaning, not just keywords
- **Intelligent Analysis**: AI insights and memory connections
- **Smart Recommendations**: AI-suggested related memories

### How to Check LLM Access
```bash
curl -X GET "https://your-ai-ide-api.example.com/protected" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Troubleshooting LLM Access
- **"LLM access not available"**: Enable LLM access for your project
- **"403 Forbidden"**: Use an admin token to enable LLM access
- **Contact admin**: If you can't enable LLM access yourself

## Resources
- [Python Quickstart Script](/onboarding/scripts/memory_quickstart.py)
- [Postman Collection](/onboarding/scripts/memory_api.postman_collection.json)
- [External Onboarding Guide](../../ONBOARDING_EXTERNAL.md)

## Troubleshooting
- **401 Unauthorized:** Check your API key.
- **404 Namespace not found:** Make sure you've created your project/namespace.
- **422 Validation error:** Check your request body for required fields.
- **"LLM access not available":** Enable LLM access for your project.

## Advanced
- See the full API reference for batch operations, metadata, and more.
- For automation, you can script onboarding by calling `/onboarding/init` and then using the memory endpoints.

---

For questions or help, contact your AI IDE API administrator or see the [main documentation](/docs). 
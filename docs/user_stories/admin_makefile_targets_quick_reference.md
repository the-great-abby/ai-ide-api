---
title: Admin Makefile Targets Quick Reference
motivation: >
  To provide a quick reference for internal project admins to manage external projects
  using friendly Makefile targets without needing to remember complex API calls or script syntax.
actors:
  - Internal Project Administrator
preconditions:
  - Admin has valid admin token
  - API is running and accessible
  - Admin has access to Makefile.ai-admin
steps:
  - Setup admin token
  - Use appropriate Makefile target for desired action
  - Verify results
expected_outcomes:
  - External projects are managed efficiently
  - LLM access is granted/revoked as needed
  - API tokens are generated and distributed
  - Project status is easily monitored
best_practices:
  - Keep admin token secure
  - Document token distribution
  - Verify changes after making them
  - Use descriptive token descriptions
---

# Admin Makefile Targets Quick Reference

## 🚀 Quick Setup

### 1. Set up your admin token:
```bash
# Option 1: Create .admin_token file (recommended)
echo 'your-admin-token-here' > .admin_token

# Option 2: Set environment variable
export ADMIN_TOKEN='your-admin-token-here'
```

### 2. Get help:
```bash
make -f Makefile.ai-admin admin-external-help
```

## 📋 Available Commands

### List All External Projects
```bash
make -f Makefile.ai-admin admin-external-list
```

### Enable LLM Access
```bash
# Using project ID (UUID)
make -f Makefile.ai-admin admin-external-enable-llm PROJECT_ID_OR_NAME=abc123-def4-5678-90ab-cdef12345678

# Using project name
make -f Makefile.ai-admin admin-external-enable-llm PROJECT_ID_OR_NAME=team-xyz-project
```

### Disable LLM Access
```bash
# Using project ID (UUID)
make -f Makefile.ai-admin admin-external-disable-llm PROJECT_ID_OR_NAME=abc123-def4-5678-90ab-cdef12345678

# Using project name
make -f Makefile.ai-admin admin-external-disable-llm PROJECT_ID_OR_NAME=team-xyz-project
```

### Generate API Token
```bash
# Basic token generation (using project name)
make -f Makefile.ai-admin admin-external-generate-token PROJECT_ID_OR_NAME=team-xyz-project

# With description
make -f Makefile.ai-admin admin-external-generate-token PROJECT_ID_OR_NAME=team-xyz-project DESCRIPTION="Team XYZ external token"

# With specific role
make -f Makefile.ai-admin admin-external-generate-token PROJECT_ID_OR_NAME=team-xyz-project ROLE=admin DESCRIPTION="Admin token for Team XYZ"
```

### Get Project Information
```bash
# Using project name
make -f Makefile.ai-admin admin-external-project-info PROJECT_ID_OR_NAME=team-xyz-project

# Using project ID
make -f Makefile.ai-admin admin-external-project-info PROJECT_ID_OR_NAME=abc123-def4-5678-90ab-cdef12345678
```

## 🔄 Common Workflows

### New External Project Setup
```bash
# 1. List projects to find the new one
make -f Makefile.ai-admin admin-external-list

# 2. Enable LLM access (using project name)
make -f Makefile.ai-admin admin-external-enable-llm PROJECT_ID_OR_NAME=team-xyz-project

# 3. Generate API token
make -f Makefile.ai-admin admin-external-generate-token PROJECT_ID_OR_NAME=team-xyz-project DESCRIPTION="Initial token for Team XYZ"

# 4. Verify setup
make -f Makefile.ai-admin admin-external-project-info PROJECT_ID_OR_NAME=team-xyz-project
```

### Revoke LLM Access
```bash
# 1. Disable LLM access (using project name)
make -f Makefile.ai-admin admin-external-disable-llm PROJECT_ID_OR_NAME=team-xyz-project

# 2. Verify change
make -f Makefile.ai-admin admin-external-project-info PROJECT_ID_OR_NAME=team-xyz-project
```

## 🎯 Project Identification

**You can use either project IDs (UUIDs) or project names:**

- **Project ID**: `abc123-def4-5678-90ab-cdef12345678`
- **Project Name**: `team-xyz-project`

**Benefits of using project names:**
- More human-readable and memorable
- Easier to type and remember
- No need to copy/paste long UUIDs
- Works the same as project IDs

## 🛠️ Troubleshooting

### "ADMIN_TOKEN not set" Error
```bash
# Solution: Create .admin_token file
echo 'your-admin-token' > .admin_token
```

### "PROJECT_ID_OR_NAME not set" Error
```bash
# Solution: Include PROJECT_ID_OR_NAME parameter
make -f Makefile.ai-admin admin-external-enable-llm PROJECT_ID_OR_NAME=team-xyz-project
```

### "Project not found" Error
```bash
# Solution: List projects to find correct name or ID
make -f Makefile.ai-admin admin-external-list
```

## 📝 Best Practices

- **Use project names** when possible - they're easier to remember and type
- Use descriptive token descriptions
- Keep `.admin_token` file secure
- Document when tokens are distributed
- Verify changes after making them 
# Memory System Security and Privacy Guide

## Overview
The memory system now includes comprehensive security and privacy controls to protect sensitive information and manage access across different projects and namespaces. This guide explains how to use these features effectively.

## Key Features

### 1. Authentication
- All memory operations require a valid API token
- Tokens can be scoped to specific projects and namespaces
- Different permission levels (read/write) for different operations

### 2. Project-Based Access Control
- Tokens can be scoped to specific projects
- Projects can control access to their namespaces
- Public namespaces are possible by setting `allowed_project_id` to null

### 3. Namespace-Level Permissions
- Fine-grained control over namespace access
- Read/write permissions for each namespace
- Support for both project-level and token-level namespace permissions

### 4. Token Scoping
- Tokens can be restricted to specific projects
- Tokens can be limited to specific namespaces
- Tokens can have different permission levels for different namespaces

## Usage Guide

### 1. Creating a Namespace Permission
```bash
curl -X POST http://localhost:9103/admin/namespace-permissions \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "project1-private",
    "project_id": "project1-uuid",
    "allowed_project_id": null,  # null means public
    "permission_type": "read"
  }'
```

### 2. Generating a Scoped Token
```bash
curl -X POST http://localhost:9103/admin/generate-token \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Project1 read-only token",
    "project_id": "project1-uuid",
    "allowed_namespaces": ["project1-private"],
    "namespace_permissions": {
      "project1-private": "read"
    }
  }'
```

### 3. Using the Token
```bash
curl -X GET http://localhost:9103/memory/nodes?namespace=project1-private \
  -H "Authorization: Bearer <project1-token>"
```

## Best Practices

### 1. Project Organization
- Use unique namespaces for each project
- Keep sensitive information in private namespaces
- Use public namespaces for shared knowledge

### 2. Token Management
- Create tokens with minimal required permissions
- Regularly rotate tokens
- Use descriptive token descriptions
- Revoke unused tokens

### 3. Namespace Design
- Use hierarchical namespace structure (e.g., `project/feature/component`)
- Document namespace purposes and access requirements
- Regularly audit namespace permissions

### 4. Security Considerations
- Never share admin tokens
- Use read-only tokens for most operations
- Implement proper error handling for permission failures
- Monitor access patterns for suspicious activity

## Common Scenarios

### 1. Project-Specific Memory
```bash
# Create a private namespace for project
curl -X POST http://localhost:9103/admin/namespace-permissions \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "project1/private",
    "project_id": "project1-uuid",
    "allowed_project_id": "project1-uuid",
    "permission_type": "write"
  }'

# Create a project-specific token
curl -X POST http://localhost:9103/admin/generate-token \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Project1 development token",
    "project_id": "project1-uuid",
    "allowed_namespaces": ["project1/private"],
    "namespace_permissions": {
      "project1/private": "write"
    }
  }'
```

### 2. Shared Knowledge Base
```bash
# Create a public namespace
curl -X POST http://localhost:9103/admin/namespace-permissions \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "shared/knowledge",
    "project_id": "shared-uuid",
    "allowed_project_id": null,
    "permission_type": "read"
  }'

# Create a read-only token for shared knowledge
curl -X POST http://localhost:9103/admin/generate-token \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Shared knowledge reader",
    "allowed_namespaces": ["shared/knowledge"],
    "namespace_permissions": {
      "shared/knowledge": "read"
    }
  }'
```

### 3. Cross-Project Collaboration
```bash
# Allow Project2 to read Project1's public data
curl -X POST http://localhost:9103/admin/namespace-permissions \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "project1/public",
    "project_id": "project1-uuid",
    "allowed_project_id": "project2-uuid",
    "permission_type": "read"
  }'
```

## Troubleshooting

### Common Issues

1. **403 Forbidden**
   - Check token permissions
   - Verify namespace access
   - Confirm project scoping

2. **401 Unauthorized**
   - Verify token is valid
   - Check token is active
   - Ensure proper Authorization header

3. **Namespace Not Found**
   - Verify namespace exists
   - Check namespace spelling
   - Confirm namespace permissions

### Debugging Steps

1. Check token permissions:
```bash
curl -X GET http://localhost:9103/admin/tokens \
  -H "Authorization: Bearer <admin-token>"
```

2. Verify namespace permissions:
```bash
curl -X GET http://localhost:9103/admin/namespace-permissions \
  -H "Authorization: Bearer <admin-token>"
```

3. Test namespace access:
```bash
curl -X GET http://localhost:9103/memory/nodes?namespace=test-namespace \
  -H "Authorization: Bearer <test-token>"
```

## References
- [Memory Graph API Documentation](docs/user_stories/ai_memory_graph_api.md)
- [API Server Code](rule_api_server.py)
- [Database Models](db.py) 
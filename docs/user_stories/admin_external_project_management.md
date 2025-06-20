---
title: Admin External Project Management
motivation: >
  To provide administrators with a simple, secure way to manage external projects,
  including enabling LLM access, generating tokens, and monitoring project status
  without requiring direct database access or complex API calls.
actors:
  - System Administrator (primary)
  - External Project Users (beneficiaries)
preconditions:
  - Admin has valid admin token
  - External projects have been created through onboarding
  - API is running and accessible
steps:
  - List External Projects:
      - Run: `python scripts/admin_external_projects.py list --admin-token <token>`
      - Review project list with LLM access status
      - Identify projects needing LLM access
  - Enable LLM Access:
      - Run: `python scripts/admin_external_projects.py enable-llm <project_id> --admin-token <token>`
      - Verify success message
      - Confirm LLM access is enabled
  - Generate API Tokens:
      - Run: `python scripts/admin_external_projects.py generate-token <project_id> --admin-token <token> --description "External project token"`
      - Copy generated token securely
      - Provide token to external project team
  - Monitor Project Status:
      - Run: `python scripts/admin_external_projects.py project-info <project_id> --admin-token <token>`
      - Review project details and settings
expected_outcomes:
  - External projects have appropriate LLM access enabled
  - API tokens are generated and distributed securely
  - Project status is easily monitored
  - External teams can use the AI IDE API effectively
best_practices:
  - Use environment variables for admin tokens in production
  - Document token distribution process
  - Regularly review project access and permissions
  - Keep admin tokens secure and rotate regularly
---

# Admin External Project Management

## Overview

This user story describes how administrators can manage external projects using the new admin interface script. This provides a secure, command-line way to handle external project administration without requiring direct database access.

## Quick Start

### Prerequisites
- Admin token with appropriate permissions
- Python environment with `requests` library
- Access to the AI IDE API

### Basic Commands

```bash
# List all external projects
python scripts/admin_external_projects.py list --admin-token <your_admin_token>

# Enable LLM access for a project
python scripts/admin_external_projects.py enable-llm <project_id> --admin-token <your_admin_token>

# Generate a new API token for a project
python scripts/admin_external_projects.py generate-token <project_id> --admin-token <your_admin_token>

# Get detailed project information
python scripts/admin_external_projects.py project-info <project_id> --admin-token <your_admin_token>
```

## Detailed Workflows

### 1. Managing LLM Access

**Scenario**: External project team requests LLM access for their project.

```bash
# Step 1: List projects to find the correct project ID
python scripts/admin_external_projects.py list --admin-token <admin_token>

# Step 2: Enable LLM access
python scripts/admin_external_projects.py enable-llm adb3ce75-b7af-4611-81a2-e06c88e2e30e --admin-token <admin_token>

# Step 3: Verify the change
python scripts/admin_external_projects.py project-info adb3ce75-b7af-4611-81a2-e06c88e2e30e --admin-token <admin_token>
```

**Expected Output**:
```
✅ LLM access enabled for project adb3ce75-b7af-4611-81a2-e06c88e2e30e
   Response: {
     "project_id": "adb3ce75-b7af-4611-81a2-e06c88e2e30e",
     "has_llm_access": true
   }
```

### 2. Token Generation and Distribution

**Scenario**: External project needs a new API token.

```bash
# Generate a new token with description
python scripts/admin_external_projects.py generate-token <project_id> \
  --admin-token <admin_token> \
  --description "External project token for team XYZ" \
  --role user
```

**Expected Output**:
```
✅ Generated token for project adb3ce75-b7af-4611-81a2-e06c88e2e30e
   Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Role: user
   LLM Access: 1
```

### 3. Project Monitoring

**Scenario**: Admin needs to review project status and settings.

```bash
# Get comprehensive project information
python scripts/admin_external_projects.py project-info <project_id> --admin-token <admin_token>
```

**Expected Output**:
```json
{
  "id": "adb3ce75-b7af-4611-81a2-e06c88e2e30e",
  "name": "external-project",
  "description": "External project for team XYZ",
  "has_llm_access": true,
  "active": true,
  "created_at": "2025-06-20T09:00:00Z",
  "default_namespace": "external-project/private",
  "namespace_prefix": "external-project"
}
```

## Security Considerations

### Admin Token Management
- Store admin tokens securely (environment variables, secure vaults)
- Rotate admin tokens regularly
- Use different admin tokens for different environments
- Never commit admin tokens to version control

### Token Distribution
- Use secure channels to distribute API tokens to external teams
- Consider using temporary tokens for initial setup
- Document token distribution process
- Implement token expiration policies

### Access Control
- Regularly review project permissions
- Disable LLM access for inactive projects
- Monitor API usage patterns
- Implement audit logging for admin actions

## Troubleshooting

### Common Issues

1. **"Admin token required" error**
   - Ensure ADMIN_TOKEN environment variable is set
   - Or use --admin-token argument
   - Verify token has admin permissions

2. **"Project not found" error**
   - Check project ID is correct
   - Use `list` command to find valid project IDs
   - Verify project exists and is active

3. **"LLM access not enabled" after enabling**
   - Check if project has active status
   - Verify admin token has sufficient permissions
   - Check API logs for detailed error messages

### Getting Help

- Check API documentation at `/docs` endpoint
- Review API logs for detailed error information
- Contact system administrator for token/permission issues
- Use `--help` flag for command documentation

## Integration with External Workflows

### Automated Token Generation
```bash
# Generate token and save to file
python scripts/admin_external_projects.py generate-token <project_id> \
  --admin-token <admin_token> \
  --description "Automated token generation" > project_token.json
```

### CI/CD Integration
```bash
# Enable LLM access in deployment pipeline
python scripts/admin_external_projects.py enable-llm $PROJECT_ID \
  --admin-token $ADMIN_TOKEN
```

### Monitoring Scripts
```bash
# Check all projects for LLM access status
python scripts/admin_external_projects.py list --admin-token <admin_token> | grep "❌ No"
```

## Best Practices Summary

1. **Use Environment Variables**: Set ADMIN_TOKEN in environment for security
2. **Document Everything**: Keep records of token distribution and access changes
3. **Regular Reviews**: Periodically audit project access and permissions
4. **Secure Distribution**: Use secure channels for token distribution
5. **Monitor Usage**: Track API usage and access patterns
6. **Backup Tokens**: Keep secure backups of critical admin tokens
7. **Test Changes**: Verify changes work as expected before production use 
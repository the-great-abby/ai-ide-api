# AI-IDE-API External Makefile

This Makefile provides easy access to common AI-IDE-API operations for external users and integrations.

## Quick Start

1. **Setup**:
   ```bash
   # Create your API token file
   echo "your-api-token-here" > .apitoken
   
   # Test connection
   make setup
   ```

2. **Basic Usage**:
   ```bash
   # Search memories
   make memory-search QUERY="docker configuration"
   
   # Create a memory
   make memory-create FILE=my_content.txt NAMESPACE=my_project
   
   # List rules
   make rule-list
   ```

## Configuration

- `API_BASE`: Base URL for the API (default: http://localhost:9103)
- `MEMORY_API_BASE`: Base URL for memory operations (default: http://localhost:9103/memory)
- `API_TOKEN`: Your API token (read from .apitoken file)

## Available Operations

### Memory Operations
- `memory-search`: Search memories with RAG
- `memory-create`: Create a new memory node
- `memory-list`: List all memory namespaces
- `memory-nodes`: List memory nodes in a namespace

### Rule Operations
- `rule-propose`: Propose a new rule
- `rule-list`: List all rules
- `rule-get`: Get a specific rule
- `rule-update`: Update a rule
- `rule-delete`: Delete a rule
- `rule-feedback`: Submit feedback on a rule

### Git History Operations
- `git-history`: Analyze recent git history
- `git-history-full`: Full git history analysis
- `git-history-summary`: Get git history summary

### Worker Operations
- `worker-trigger-enrichment`: Trigger memory enrichment
- `worker-trigger-cleanup`: Trigger memory cleanup
- `worker-trigger-similarity`: Trigger memory similarity
- `worker-status`: Get worker status
- `worker-logs`: Get worker logs

### System Operations
- `health-check`: Check system health
- `api-status`: Get detailed API status
- `system-info`: Get system information

### Backup and Restore
- `backup-memories`: Backup all memories
- `backup-rules`: Backup all rules
- `restore-memories`: Restore memories from backup
- `restore-rules`: Restore rules from backup

### Export and Import
- `export-rules`: Export rules to portable format
- `import-rules`: Import rules from portable format

## Examples

```bash
# Search for docker-related content
make memory-search QUERY="docker compose configuration"

# Create a memory from a file
make memory-create FILE=documentation.txt NAMESPACE=docs

# Propose a new rule
make rule-propose FILE=my_rule.mdc

# Analyze git history
make git-history SINCE="1 week ago" MAX_COMMITS=50

# Trigger memory enrichment
make worker-trigger-enrichment SCOPE=all

# Backup everything
make backup-memories FILE=memories_backup.json
make backup-rules FILE=rules_backup.json
```

## Testing

```bash
# Test all components
make test-connection
make test-memory
make test-rules
make test-workers

# Run example workflow
make example-workflow
```

## Dependencies

- `curl`: For HTTP requests
- `jq`: For JSON formatting (install with `brew install jq` on macOS)
- `make`: Should be available on most systems

Install dependencies:
```bash
make install-deps
```

## Troubleshooting

1. **Authentication Error**: Check your `.apitoken` file
2. **Connection Error**: Verify the API is running and accessible
3. **Missing Dependencies**: Run `make install-deps`

## Generated on

2025-06-20 06:55:39

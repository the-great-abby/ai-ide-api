#!/usr/bin/env python3
"""
Generate External Makefile for AI-IDE-API
Creates a comprehensive Makefile with all common commands and curl calls
for external users to interact with the AI-IDE-API system.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuration
DEFAULT_API_BASE = "http://localhost:9103"
DEFAULT_MEMORY_API_BASE = "http://localhost:9103/memory"

def generate_makefile(api_base: str, memory_api_base: str, output_file: str = "Makefile.external") -> str:
    """Generate a comprehensive Makefile for external AI-IDE-API usage."""
    
    makefile_content = f"""# AI-IDE-API External Makefile
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 
# This Makefile provides easy access to common AI-IDE-API operations
# for external users and integrations.
#
# Usage: make <target> [VARIABLE=value]
# Example: make memory-search QUERY="docker configuration"
# Example: make rule-propose FILE=my_rule.mdc

# Configuration
API_BASE ?= {api_base}
MEMORY_API_BASE ?= {memory_api_base}
API_TOKEN ?= $(shell cat .apitoken 2>/dev/null || echo "")
QUERY ?= "test query"
FILE ?= ""
NAMESPACE ?= "external"
SCOPE ?= "all"
DRY_RUN ?= false

# Colors for output
GREEN = \\033[0;32m
YELLOW = \\033[1;33m
RED = \\033[0;31m
NC = \\033[0m # No Color

.PHONY: help setup auth memory-search memory-create memory-list memory-nodes memory-namespaces \\
        rule-propose rule-list rule-get rule-update rule-delete rule-feedback \\
        git-history git-history-full git-history-summary \\
        worker-trigger-enrichment worker-trigger-cleanup worker-trigger-similarity \\
        worker-status worker-logs \\
        health-check api-status system-info \\
        backup-memories backup-rules restore-memories restore-rules \\
        export-rules import-rules \\
        test-connection test-memory test-rules test-workers

# =============================================================================
# HELP AND SETUP
# =============================================================================

help: ## Show this help message
	@echo "$(GREEN)AI-IDE-API External Makefile$(NC)"
	@echo "Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
	@echo ""
	@echo "$(YELLOW)Configuration:$(NC)"
	@echo "  API_BASE=$(API_BASE)"
	@echo "  MEMORY_API_BASE=$(MEMORY_API_BASE)"
	@echo "  API_TOKEN=$(if $(API_TOKEN),***set***,not set)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {{FS = ":.*?## "}}; {{printf "  $(GREEN)%-25s$(NC) %s\\n", $$1, $$2}}'

setup: ## Initial setup - check connection and create token file
	@echo "$(GREEN)Setting up AI-IDE-API connection...$(NC)"
	@if [ ! -f .apitoken ]; then \\
		echo "$(YELLOW)No .apitoken file found. Please create one with your API token.$(NC)"; \\
		echo "Example: echo 'your-token-here' > .apitoken"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Testing connection...$(NC)"
	@make test-connection
	@echo "$(GREEN)Setup complete!$(NC)"

auth: ## Test authentication and show current token info
	@echo "$(GREEN)Testing authentication...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/health" | jq . || \\
		echo "$(RED)Authentication failed. Check your API_TOKEN.$(NC)"

# =============================================================================
# MEMORY OPERATIONS
# =============================================================================

memory-search: ## Search memories with RAG (QUERY=your search query)
	@echo "$(GREEN)Searching memories for: $(QUERY)$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" \\
		"$(MEMORY_API_BASE)/rag-search?query=$(QUERY)" | jq .

memory-create: ## Create a new memory node (FILE=content file, NAMESPACE=namespace)
	@if [ -z "$(FILE)" ]; then \\
		echo "$(RED)Error: FILE parameter required$(NC)"; \\
		echo "Usage: make memory-create FILE=my_content.txt NAMESPACE=my_namespace"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Creating memory from file: $(FILE)$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(MEMORY_API_BASE)/nodes" \\
		-d '{{"namespace": "$(NAMESPACE)", "content": "$(shell cat $(FILE))"}}' | jq .

memory-list: ## List all memory namespaces
	@echo "$(GREEN)Listing memory namespaces...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(MEMORY_API_BASE)/namespaces" | jq .

memory-nodes: ## List memory nodes in a namespace (NAMESPACE=namespace)
	@echo "$(GREEN)Listing memory nodes in namespace: $(NAMESPACE)$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(MEMORY_API_BASE)/nodes?namespace=$(NAMESPACE)" | jq .

memory-namespaces: ## Get detailed info about all namespaces
	@echo "$(GREEN)Getting namespace details...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(MEMORY_API_BASE)/namespaces" | jq .

# =============================================================================
# RULE OPERATIONS
# =============================================================================

rule-propose: ## Propose a new rule (FILE=rule.mdc file)
	@if [ -z "$(FILE)" ]; then \\
		echo "$(RED)Error: FILE parameter required$(NC)"; \\
		echo "Usage: make rule-propose FILE=my_rule.mdc"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Proposing rule from file: $(FILE)$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(API_BASE)/rules/proposals" \\
		-d '{{"rule_file": "$(shell cat $(FILE))"}}' | jq .

rule-list: ## List all rules
	@echo "$(GREEN)Listing all rules...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/rules" | jq .

rule-get: ## Get a specific rule (RULE_ID=rule_id)
	@if [ -z "$(RULE_ID)" ]; then \\
		echo "$(RED)Error: RULE_ID parameter required$(NC)"; \\
		echo "Usage: make rule-get RULE_ID=rule_id_here"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Getting rule: $(RULE_ID)$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/rules/$(RULE_ID)" | jq .

rule-update: ## Update a rule (RULE_ID=rule_id, FILE=updated_rule.mdc)
	@if [ -z "$(RULE_ID)" ] || [ -z "$(FILE)" ]; then \\
		echo "$(RED)Error: RULE_ID and FILE parameters required$(NC)"; \\
		echo "Usage: make rule-update RULE_ID=rule_id FILE=updated_rule.mdc"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Updating rule: $(RULE_ID)$(NC)"
	@curl -s -X PUT -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(API_BASE)/rules/$(RULE_ID)" \\
		-d '{{"rule_file": "$(shell cat $(FILE))"}}' | jq .

rule-delete: ## Delete a rule (RULE_ID=rule_id)
	@if [ -z "$(RULE_ID)" ]; then \\
		echo "$(RED)Error: RULE_ID parameter required$(NC)"; \\
		echo "Usage: make rule-delete RULE_ID=rule_id_here"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Deleting rule: $(RULE_ID)$(NC)"
	@curl -s -X DELETE -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/rules/$(RULE_ID)" | jq .

rule-feedback: ## Submit feedback on a rule (RULE_ID=rule_id, FEEDBACK=feedback_text)
	@if [ -z "$(RULE_ID)" ] || [ -z "$(FEEDBACK)" ]; then \\
		echo "$(RED)Error: RULE_ID and FEEDBACK parameters required$(NC)"; \\
		echo "Usage: make rule-feedback RULE_ID=rule_id FEEDBACK='your feedback'"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Submitting feedback for rule: $(RULE_ID)$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(API_BASE)/rules/$(RULE_ID)/feedback" \\
		-d '{{"feedback": "$(FEEDBACK)"}}' | jq .

# =============================================================================
# GIT HISTORY OPERATIONS
# =============================================================================

git-history: ## Analyze recent git history (SINCE=1 week ago, MAX_COMMITS=20)
	@echo "$(GREEN)Analyzing git history since: $(SINCE)$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(API_BASE)/git-history/analyze" \\
		-d '{{"since": "$(SINCE)", "max_commits": $(MAX_COMMITS), "create_memory": true}}' | jq .

git-history-full: ## Full git history analysis (since 2020, 1000 commits)
	@echo "$(GREEN)Running full git history analysis...$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(API_BASE)/git-history/analyze" \\
		-d '{{"since": "2020-01-01", "max_commits": 1000, "create_memory": true, "memory_namespace": "git_history_full"}}' | jq .

git-history-summary: ## Get git history summary
	@echo "$(GREEN)Getting git history summary...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/git-history/summary" | jq .

# =============================================================================
# WORKER OPERATIONS
# =============================================================================

worker-trigger-enrichment: ## Trigger memory enrichment job (SCOPE=all)
	@echo "$(GREEN)Triggering memory enrichment job...$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(API_BASE)/workers/trigger" \\
		-d '{{"job_type": "memory_enrichment", "scope": "$(SCOPE)"}}' | jq .

worker-trigger-cleanup: ## Trigger memory cleanup job (SCOPE=all)
	@echo "$(GREEN)Triggering memory cleanup job...$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(API_BASE)/workers/trigger" \\
		-d '{{"job_type": "memory_cleanup", "scope": "$(SCOPE)"}}' | jq .

worker-trigger-similarity: ## Trigger memory similarity job (SCOPE=all)
	@echo "$(GREEN)Triggering memory similarity job...$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(API_BASE)/workers/trigger" \\
		-d '{{"job_type": "memory_similarity", "scope": "$(SCOPE)"}}' | jq .

worker-status: ## Get worker status
	@echo "$(GREEN)Getting worker status...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/workers/status" | jq .

worker-logs: ## Get recent worker logs (LINES=50)
	@echo "$(GREEN)Getting worker logs...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/workers/logs?lines=$(LINES)" | jq .

# =============================================================================
# SYSTEM OPERATIONS
# =============================================================================

health-check: ## Check system health
	@echo "$(GREEN)Checking system health...$(NC)"
	@curl -s "$(API_BASE)/health" | jq .

api-status: ## Get detailed API status
	@echo "$(GREEN)Getting API status...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/status" | jq .

system-info: ## Get system information
	@echo "$(GREEN)Getting system information...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/system/info" | jq .

# =============================================================================
# BACKUP AND RESTORE
# =============================================================================

backup-memories: ## Backup all memories to file (FILE=backup.json)
	@echo "$(GREEN)Backing up memories to: $(FILE)$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(MEMORY_API_BASE)/backup" | jq . > $(FILE)

backup-rules: ## Backup all rules to file (FILE=rules_backup.json)
	@echo "$(GREEN)Backing up rules to: $(FILE)$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/rules/backup" | jq . > $(FILE)

restore-memories: ## Restore memories from file (FILE=backup.json)
	@if [ -z "$(FILE)" ]; then \\
		echo "$(RED)Error: FILE parameter required$(NC)"; \\
		echo "Usage: make restore-memories FILE=backup.json"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Restoring memories from: $(FILE)$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(MEMORY_API_BASE)/restore" -d @$(FILE) | jq .

restore-rules: ## Restore rules from file (FILE=rules_backup.json)
	@if [ -z "$(FILE)" ]; then \\
		echo "$(RED)Error: FILE parameter required$(NC)"; \\
		echo "Usage: make restore-rules FILE=rules_backup.json"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Restoring rules from: $(FILE)$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(API_BASE)/rules/restore" -d @$(FILE) | jq .

# =============================================================================
# EXPORT AND IMPORT
# =============================================================================

export-rules: ## Export rules to portable format (FILE=rules_export.json)
	@echo "$(GREEN)Exporting rules to: $(FILE)$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/rules/export" | jq . > $(FILE)

import-rules: ## Import rules from portable format (FILE=rules_export.json)
	@if [ -z "$(FILE)" ]; then \\
		echo "$(RED)Error: FILE parameter required$(NC)"; \\
		echo "Usage: make import-rules FILE=rules_export.json"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Importing rules from: $(FILE)$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" -H "Content-Type: application/json" \\
		"$(API_BASE)/rules/import" -d @$(FILE) | jq .

# =============================================================================
# TESTING
# =============================================================================

test-connection: ## Test basic connection to API
	@echo "$(GREEN)Testing connection to $(API_BASE)...$(NC)"
	@curl -s "$(API_BASE)/health" > /dev/null && \\
		echo "$(GREEN)✓ Connection successful$(NC)" || \\
		echo "$(RED)✗ Connection failed$(NC)"

test-memory: ## Test memory API functionality
	@echo "$(GREEN)Testing memory API...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(MEMORY_API_BASE)/namespaces" > /dev/null && \\
		echo "$(GREEN)✓ Memory API working$(NC)" || \\
		echo "$(RED)✗ Memory API failed$(NC)"

test-rules: ## Test rules API functionality
	@echo "$(GREEN)Testing rules API...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/rules" > /dev/null && \\
		echo "$(GREEN)✓ Rules API working$(NC)" || \\
		echo "$(RED)✗ Rules API failed$(NC)"

test-workers: ## Test worker API functionality
	@echo "$(GREEN)Testing worker API...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" "$(API_BASE)/workers/status" > /dev/null && \\
		echo "$(GREEN)✓ Worker API working$(NC)" || \\
		echo "$(RED)✗ Worker API failed$(NC)"

# =============================================================================
# UTILITY TARGETS
# =============================================================================

clean: ## Clean up temporary files
	@echo "$(GREEN)Cleaning up...$(NC)"
	@rm -f *.json *.backup *.export

install-deps: ## Install required dependencies (jq, curl)
	@echo "$(GREEN)Checking dependencies...$(NC)"
	@which jq > /dev/null || (echo "$(YELLOW)Installing jq...$(NC)" && brew install jq)
	@which curl > /dev/null || (echo "$(RED)curl not found. Please install curl.$(NC)" && exit 1)
	@echo "$(GREEN)✓ Dependencies ready$(NC)"

# =============================================================================
# EXAMPLES
# =============================================================================

example-search: ## Example: Search for docker-related memories
	@make memory-search QUERY="docker configuration and setup"

example-create: ## Example: Create a memory from a text file
	@echo "This is an example memory content." > example_memory.txt
	@make memory-create FILE=example_memory.txt NAMESPACE=examples
	@rm example_memory.txt

example-rule: ## Example: Create and propose a simple rule
	@echo "# Example Rule" > example_rule.mdc
	@echo "This is an example rule content." >> example_rule.mdc
	@make rule-propose FILE=example_rule.mdc
	@rm example_rule.mdc

example-workflow: ## Example: Complete workflow (search, create, analyze)
	@echo "$(GREEN)Running example workflow...$(NC)"
	@make test-connection
	@make memory-search QUERY="example workflow"
	@make example-create
	@make git-history SINCE="1 day ago" MAX_COMMITS=5
	@echo "$(GREEN)Example workflow complete!$(NC)"
"""
    
    return makefile_content

def generate_readme(api_base: str, memory_api_base: str) -> str:
    """Generate a README file for the external Makefile."""
    
    readme_content = f"""# AI-IDE-API External Makefile

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

- `API_BASE`: Base URL for the API (default: {api_base})
- `MEMORY_API_BASE`: Base URL for memory operations (default: {memory_api_base})
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

{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return readme_content

def main():
    parser = argparse.ArgumentParser(description="Generate external Makefile for AI-IDE-API")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="API base URL")
    parser.add_argument("--memory-api-base", default=DEFAULT_MEMORY_API_BASE, help="Memory API base URL")
    parser.add_argument("--output", default="Makefile.external", help="Output Makefile name")
    parser.add_argument("--readme", action="store_true", help="Also generate README.md")
    
    args = parser.parse_args()
    
    print(f"Generating external Makefile...")
    print(f"API Base: {args.api_base}")
    print(f"Memory API Base: {args.memory_api_base}")
    print(f"Output: {args.output}")
    
    # Generate Makefile
    makefile_content = generate_makefile(args.api_base, args.memory_api_base, args.output)
    
    with open(args.output, "w") as f:
        f.write(makefile_content)
    
    print(f"✅ Generated {args.output}")
    
    # Generate README if requested
    if args.readme:
        readme_content = generate_readme(args.api_base, args.memory_api_base)
        with open("README.external.md", "w") as f:
            f.write(readme_content)
        print("✅ Generated README.external.md")
    
    print("\n🎉 External Makefile generation complete!")
    print(f"\nNext steps:")
    print(f"1. Create your API token: echo 'your-token' > .apitoken")
    print(f"2. Test connection: make -f {args.output} setup")
    print(f"3. Start using: make -f {args.output} help")

if __name__ == "__main__":
    main() 
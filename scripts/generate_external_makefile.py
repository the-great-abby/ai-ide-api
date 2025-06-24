#!/usr/bin/env python3
"""
Generate external Makefile for AI-IDE-API

This script generates a focused, project-specific Makefile for external projects
to interact with the AI-IDE-API. The generated Makefile includes essential
operations like connection testing, LLM access checking, and health monitoring.

Usage:
    python scripts/generate_external_makefile.py --api-base <url> --output <filename>
    python scripts/generate_external_makefile.py --help
"""

import argparse
import os
import sys
from datetime import datetime

def generate_makefile(api_base: str, memory_api_base: str, output_file: str = "Makefile.external") -> str:
    """Generate a focused Makefile for external AI-IDE-API usage."""
    
    # Extract project name from output file or use default
    project_name = output_file.replace('Makefile', '').replace('makefile', '').strip('_') or 'external_project'
    
    # Use placeholder for API token that users need to replace
    api_token = "$(shell cat .apitoken 2>/dev/null || echo 'YOUR_API_TOKEN_HERE')"
    admin_token = "$(shell cat .api_admin_token 2>/dev/null || echo '')"
    project_id_var = '$(shell cat .projectname 2>/dev/null || echo "")'
    
    makefile_content = f'''# External Project Makefile for AI IDE API Integration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Project: {project_name}

# Configuration
API_BASE_URL = {api_base}
API_TOKEN = {api_token}
ADMIN_TOKEN = {admin_token}
PROJECT_IDENTIFIER = {project_id_var}  # Project name or ID (from .projectname)

# Colors for output
GREEN = \\033[0;32m
YELLOW = \\033[1;33m
RED = \\033[0;31m
NC = \\033[0m # No Color

# Default target
.PHONY: help
help:
	@echo "$(GREEN)Available commands:$(NC)"
	@echo "  $(YELLOW)test-connection$(NC)     - Test API connection and authentication"
	@echo "  $(YELLOW)check-llm-access$(NC)     - Check if project has LLM access enabled"
	@echo "  $(YELLOW)request-llm-access$(NC)   - Show instructions for requesting LLM access"
	@echo "  $(YELLOW)health$(NC)               - Check API health status"
	@echo "  $(YELLOW)memory-create$(NC)        - Create a memory node in project namespace"
	@echo "  $(YELLOW)memory-list$(NC)          - List memory nodes in project namespace"
	@echo "  $(YELLOW)summarize-git-diff$(NC)   - Summarize a git diff using LLM"
	@echo "  $(YELLOW)help$(NC)                 - Show this help message"
	@if [ -f .api_admin_token ]; then \\
		echo ""; \\
		echo "$(GREEN)Admin commands (available with admin token):$(NC)"; \\
		echo "  $(YELLOW)admin-enable-llm$(NC)   - Enable LLM access for this project (by name or ID)"; \\
		echo "  $(YELLOW)admin-disable-llm$(NC)  - Disable LLM access for this project (by name or ID)"; \\
		echo "  $(YELLOW)admin-generate-token$(NC) - Generate new token for this project (by name or ID)"; \\
		echo "  $(YELLOW)admin-project-info$(NC) - Show project information"; \\
		echo "  $(YELLOW)admin-grant-read-permission$(NC) - Grant read permission to project namespace"; \\
		echo "  $(YELLOW)admin-grant-write-permission$(NC) - Grant write permission to project namespace"; \\
	fi

# Test API connection and authentication
.PHONY: test-connection
test-connection:
	@echo "$(GREEN)Testing API connection...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" \\
		"$(API_BASE_URL)/protected" | jq . || echo "$(RED)Connection failed$(NC)"

# Check LLM access status
.PHONY: check-llm-access
check-llm-access:
	@echo "$(GREEN)Checking LLM access status...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" \\
		"$(API_BASE_URL)/protected" | jq -r '.token_info.has_llm_access' | \\
		if [ "$$(cat)" = "1" ]; then \\
			echo "$(GREEN)✅ LLM access is ENABLED$(NC)"; \\
		else \\
			echo "$(RED)❌ LLM access is DISABLED$(NC)"; \\
		fi

# Show instructions for requesting LLM access
.PHONY: request-llm-access
request-llm-access:
	@echo "$(YELLOW)To request LLM access for this project:$(NC)"
	@echo "1. Contact the AI IDE API administrator"
	@echo "2. Provide your project ID: $(YELLOW)$$(curl -s -H 'Authorization: Bearer $(API_TOKEN)' '$(API_BASE_URL)/protected' | jq -r '.token_info.project_id')$(NC)"
	@echo "3. Request LLM access to be enabled"
	@echo ""
	@echo "You can check current status with: $(YELLOW)make check-llm-access$(NC)"

# Check API health
.PHONY: health
health:
	@echo "$(GREEN)Checking API health...$(NC)"
	@curl -s "$(API_BASE_URL)/health" | jq . || echo "$(RED)Health check failed$(NC)"

# Admin commands (only available if .api_admin_token exists)
.PHONY: admin-enable-llm
admin-enable-llm:
	@if [ ! -f .api_admin_token ]; then \\
		echo "$(RED)Admin token not found. Create .api_admin_token file first.$(NC)"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Enabling LLM access for this project...$(NC)"
	# The API requires both project_id and name fields in the body
	@curl -s -X POST -H "Authorization: Bearer $(ADMIN_TOKEN)" \\
		-H "Content-Type: application/json" \\
		"$(API_BASE_URL)/memory/admin/project/llm-access" \\
		-d '{{"project_id": "$(PROJECT_IDENTIFIER)", "name": "$(PROJECT_IDENTIFIER)", "has_llm_access": true}}' | jq .

.PHONY: admin-disable-llm
admin-disable-llm:
	@if [ ! -f .api_admin_token ]; then \\
		echo "$(RED)Admin token not found. Create .api_admin_token file first.$(NC)"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Disabling LLM access for this project...$(NC)"
	# The API requires both project_id and name fields in the body
	@curl -s -X POST -H "Authorization: Bearer $(ADMIN_TOKEN)" \\
		-H "Content-Type: application/json" \\
		"$(API_BASE_URL)/memory/admin/project/llm-access" \\
		-d '{{"project_id": "$(PROJECT_IDENTIFIER)", "name": "$(PROJECT_IDENTIFIER)", "has_llm_access": false}}' | jq .

.PHONY: admin-generate-token
admin-generate-token:
	@if [ ! -f .api_admin_token ]; then \\
		echo "$(RED)Admin token not found. Create .api_admin_token file first.$(NC)"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Generating new token for this project...$(NC)"
	@echo "Usage: make admin-generate-token DESCRIPTION='token description' ROLE=user|admin"
	@if [ -n "$(DESCRIPTION)" ]; then \\
		curl -s -X POST -H "Authorization: Bearer $(ADMIN_TOKEN)" \\
			-H "Content-Type: application/json" \\
			"$(API_BASE_URL)/admin/generate-token" \\
			-d '{{"description": "$(DESCRIPTION)", "role": "$(ROLE)", "project_id": "$(PROJECT_IDENTIFIER)"}}' | jq .; \\
	else \\
		echo "$(YELLOW)Example: make admin-generate-token DESCRIPTION='New user token' ROLE=user$(NC)"; \\
	fi

.PHONY: admin-project-info
admin-project-info:
	@if [ ! -f .api_admin_token ]; then \\
		echo "$(RED)Admin token not found. Create .api_admin_token file first.$(NC)"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Getting project information...$(NC)"
	@echo "$(YELLOW)Note: Direct project info endpoint not available. Use test-connection to see token info.$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" \\
		"$(API_BASE_URL)/protected" | jq .

# Grant read permission to project namespace
.PHONY: admin-grant-read-permission
admin-grant-read-permission:
	@if [ ! -f .api_admin_token ]; then \\
		echo "$(RED)Admin token not found. Create .api_admin_token file first.$(NC)"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Granting READ permission for project namespace...$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(ADMIN_TOKEN)" \\
		-H "Content-Type: application/json" \\
		"$(API_BASE_URL)/memory/admin/namespace-permissions" \\
		-d '{{"namespace": "$(PROJECT_IDENTIFIER)", "project_id": "$(PROJECT_IDENTIFIER)", "permission_type": "read"}}' | jq .

# Grant write permission to project namespace
.PHONY: admin-grant-write-permission
admin-grant-write-permission:
	@if [ ! -f .api_admin_token ]; then \\
		echo "$(RED)Admin token not found. Create .api_admin_token file first.$(NC)"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Granting WRITE permission for project namespace...$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(ADMIN_TOKEN)" \\
		-H "Content-Type: application/json" \\
		"$(API_BASE_URL)/memory/admin/namespace-permissions" \\
		-d '{{"namespace": "$(PROJECT_IDENTIFIER)", "project_id": "$(PROJECT_IDENTIFIER)", "permission_type": "write"}}' | jq .

# User target: create a memory node in the project namespace
.PHONY: memory-create
memory-create:
	@if [ -z "$(CONTENT)" ]; then \\
		echo "$(YELLOW)Usage: make memory-create CONTENT='your text' [META='meta info']$(NC)"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Creating memory node in project namespace...$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" \\
		-H "Content-Type: application/json" \\
		"$(API_BASE_URL)/memory/nodes" \\
		-d '{{"content": "$(CONTENT)", "namespace": "$(PROJECT_IDENTIFIER)", "meta": "$(META)"}}' | jq .

# User target: list memory nodes in the project namespace
.PHONY: memory-list
memory-list:
	@echo "$(GREEN)Listing memory nodes in project namespace...$(NC)"
	@curl -s -H "Authorization: Bearer $(API_TOKEN)" \\
		"$(API_BASE_URL)/memory/nodes?namespace=$(PROJECT_IDENTIFIER)" | jq .

# User target: summarize a git diff using LLM
.PHONY: summarize-git-diff
summarize-git-diff:
	@if [ -z "$(DIFF)" ]; then \\
		echo "$(YELLOW)Usage: make summarize-git-diff DIFF='your git diff' [CONCISE=true|false]$(NC)"; \\
		exit 1; \\
	fi
	@echo "$(GREEN)Summarizing git diff using LLM...$(NC)"
	@curl -s -X POST -H "Authorization: Bearer $(API_TOKEN)" \\
		-H "Content-Type: application/json" \\
		"$(API_BASE_URL)/summarize-git-diff" \\
		-d '{{"diff": "$(DIFF)", "concise": $(CONCISE)}}' | jq .
'''
    
    return makefile_content

def main():
    parser = argparse.ArgumentParser(description="Generate external Makefile for AI-IDE-API")
    parser.add_argument("--api-base", default="http://localhost:9103", help="API base URL")
    parser.add_argument("--memory-api-base", help="Memory API base URL (auto-detected if not provided)")
    parser.add_argument("--output", default="Makefile.external", help="Output Makefile name")
    parser.add_argument("--readme", action="store_true", help="Also generate README.md (deprecated)")

    args = parser.parse_args()
    
    # Auto-detect memory API base if not provided
    memory_api_base = args.memory_api_base or f"{args.api_base}/memory"
    
    print("Generating external Makefile...")
    print(f"API Base: {args.api_base}")
    print(f"Memory API Base: {memory_api_base}")
    print(f"Output: {args.output}")
    
    # Generate Makefile content
    makefile_content = generate_makefile(args.api_base, memory_api_base, args.output)
    
    # Write Makefile
    with open(args.output, "w") as f:
        f.write(makefile_content)
    
    print(f"✅ Generated {args.output}")
    
    if args.readme:
        print("⚠️  README generation is deprecated. Focus on the Makefile for essential operations.")
    
    print("\n🎉 External Makefile generation complete!")
    print("\nNext steps:")
    print("1. Create your API token: echo 'your-token' > .apitoken")
    print(f"2. Test connection: make -f {args.output} test-connection")
    print(f"3. Start using: make -f {args.output} help")

if __name__ == "__main__":
    main() 
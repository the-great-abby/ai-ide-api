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
    
    makefile_content = f'''# External Project Makefile for AI IDE API Integration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Project: {project_name}

# Configuration
API_BASE_URL = {api_base}
API_TOKEN = {api_token}

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
	@echo "  $(YELLOW)help$(NC)                 - Show this help message"

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
		"$(API_BASE_URL)/memory/admin/project/llm-access" | jq . || echo "$(RED)Failed to check LLM access$(NC)"

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
#!/usr/bin/env python3
"""
Admin interface for managing external projects in the AI IDE API.

This script provides a simple command-line interface for administrators
to manage external projects, including:
- Listing all projects
- Enabling/disabling LLM access
- Generating API tokens
- Viewing project details

Usage:
    python scripts/admin_external_projects.py list
    python scripts/admin_external_projects.py enable-llm <project_id_or_name>
    python scripts/admin_external_projects.py disable-llm <project_id_or_name>
    python scripts/admin_external_projects.py generate-token <project_id_or_name>
    python scripts/admin_external_projects.py project-info <project_id_or_name>
"""

import argparse
import json
import requests
import sys
from typing import Optional, Dict, Any


class ExternalProjectAdmin:
    def __init__(self, api_base: str, admin_token: str):
        self.api_base = api_base.rstrip('/')
        self.admin_token = admin_token
        self.headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

    def list_projects(self) -> Dict[str, Any]:
        """List all projects."""
        try:
            response = requests.get(f"{self.api_base}/projects", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error listing projects: {e}")
            return {}

    def get_project_info(self, project_identifier: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific project by ID or name."""
        try:
            response = requests.get(f"{self.api_base}/projects/{project_identifier}", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting project info: {e}")
            return None

    def enable_llm_access(self, project_identifier: str) -> bool:
        """Enable LLM access for a project by ID or name."""
        try:
            # First get the project info to resolve the ID
            project_info = self.get_project_info(project_identifier)
            if not project_info:
                print(f"❌ Error: Could not find project '{project_identifier}'")
                return False
            
            project_id = project_info.get('id')
            project_name = project_info.get('name', project_identifier)
            
            payload = {"project_id": project_id, "has_llm_access": True}
            response = requests.post(
                f"{self.api_base}/memory/admin/project/llm-access",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ LLM access enabled for project '{project_name}' (ID: {project_id})")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error enabling LLM access: {e}")
            return False

    def disable_llm_access(self, project_identifier: str) -> bool:
        """Disable LLM access for a project by ID or name."""
        try:
            # First get the project info to resolve the ID
            project_info = self.get_project_info(project_identifier)
            if not project_info:
                print(f"❌ Error: Could not find project '{project_identifier}'")
                return False
            
            project_id = project_info.get('id')
            project_name = project_info.get('name', project_identifier)
            
            payload = {"project_id": project_id, "has_llm_access": False}
            response = requests.post(
                f"{self.api_base}/memory/admin/project/llm-access",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ LLM access disabled for project '{project_name}' (ID: {project_id})")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error disabling LLM access: {e}")
            return False

    def generate_token(self, project_identifier: str, description: str = "", role: str = "user") -> Optional[str]:
        """Generate an API token for a project by ID or name."""
        try:
            # First get the project info to resolve the ID
            project_info = self.get_project_info(project_identifier)
            if not project_info:
                print(f"❌ Error: Could not find project '{project_identifier}'")
                return None
            
            project_id = project_info.get('id')
            project_name = project_info.get('name', project_identifier)
            
            payload = {
                "description": description or f"External project token for {project_name}",
                "role": role,
                "project_id": project_id
            }
            response = requests.post(
                f"{self.api_base}/admin/generate-token",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Generated token for project '{project_name}' (ID: {project_id})")
            print(f"   Token: {result.get('token', 'N/A')}")
            print(f"   Role: {result.get('role', 'N/A')}")
            print(f"   LLM Access: {result.get('has_llm_access', 'N/A')}")
            return result.get('token')
        except requests.exceptions.RequestException as e:
            print(f"❌ Error generating token: {e}")
            return None

    def display_projects_table(self, projects: list):
        """Display projects in a nice table format."""
        if not projects:
            print("No projects found.")
            return

        print("\n📋 External Projects")
        print("=" * 80)
        print(f"{'ID':<36} {'Name':<20} {'LLM Access':<10} {'Active':<8} {'Created':<12}")
        print("-" * 80)
        
        for project in projects:
            project_id = project.get('id', 'N/A')[:36]
            name = project.get('name', 'N/A')[:20]
            llm_access = "✅ Yes" if project.get('has_llm_access') else "❌ No"
            active = "✅ Yes" if project.get('active') else "❌ No"
            created = project.get('created_at', 'N/A')[:10] if project.get('created_at') else 'N/A'
            
            print(f"{project_id:<36} {name:<20} {llm_access:<10} {active:<8} {created:<12}")


def main():
    parser = argparse.ArgumentParser(description="Admin interface for external projects")
    parser.add_argument("command", choices=[
        "list", "enable-llm", "disable-llm", "generate-token", "project-info"
    ], help="Command to execute")
    parser.add_argument("project_identifier", nargs="?", help="Project ID or name (required for most commands)")
    parser.add_argument("--api-base", default="http://localhost:9103", help="API base URL")
    parser.add_argument("--admin-token", help="Admin token (or set ADMIN_TOKEN env var)")
    parser.add_argument("--description", help="Token description (for generate-token)")
    parser.add_argument("--role", default="user", choices=["user", "admin"], help="Token role (for generate-token)")

    args = parser.parse_args()

    # Get admin token from args or environment
    admin_token = args.admin_token or os.environ.get('ADMIN_TOKEN')
    if not admin_token:
        print("❌ Error: Admin token required. Use --admin-token or set ADMIN_TOKEN environment variable.")
        sys.exit(1)

    admin = ExternalProjectAdmin(args.api_base, admin_token)

    if args.command == "list":
        projects = admin.list_projects()
        if isinstance(projects, list):
            admin.display_projects_table(projects)
        else:
            print("❌ Error: Could not retrieve projects")

    elif args.command == "project-info":
        if not args.project_identifier:
            print("❌ Error: Project ID or name required")
            sys.exit(1)
        project_info = admin.get_project_info(args.project_identifier)
        if project_info:
            print(f"\n📊 Project Information for '{args.project_identifier}'")
            print("=" * 50)
            print(json.dumps(project_info, indent=2))
        else:
            print("❌ Error: Could not retrieve project information")

    elif args.command == "enable-llm":
        if not args.project_identifier:
            print("❌ Error: Project ID or name required")
            sys.exit(1)
        admin.enable_llm_access(args.project_identifier)

    elif args.command == "disable-llm":
        if not args.project_identifier:
            print("❌ Error: Project ID or name required")
            sys.exit(1)
        admin.disable_llm_access(args.project_identifier)

    elif args.command == "generate-token":
        if not args.project_identifier:
            print("❌ Error: Project ID or name required")
            sys.exit(1)
        admin.generate_token(args.project_identifier, args.description, args.role)


if __name__ == "__main__":
    import os
    main() 
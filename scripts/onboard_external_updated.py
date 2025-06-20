#!/usr/bin/env python3
"""
Updated External Onboarding Script for AI-IDE-API
Provides a comprehensive onboarding experience for external users,
including Makefile generation and interactive setup.
"""

import argparse
import json
import os
import sys
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
DEFAULT_API_BASE = "http://localhost:9103"
DEFAULT_MEMORY_API_BASE = "http://localhost:9103/memory"

class ExternalOnboarding:
    def __init__(self, api_base: str, memory_api_base: str):
        self.api_base = api_base
        self.memory_api_base = memory_api_base
        self.token = None
        self.project_name = None
        self.team_name = None
        self.user_email = None
        self.project_id = None
        self.team_id = None
        
    def print_banner(self):
        """Print the onboarding banner."""
        print("=" * 80)
        print("🏴‍☠️  AI-IDE-API External Onboarding")
        print("=" * 80)
        print("Welcome to the AI-IDE-API system! This script will help you")
        print("set up everything you need to interact with the API.")
        print("=" * 80)
        print()
        
    def get_project_info(self):
        """Get basic project information from the user."""
        print("📋 Project Information")
        print("-" * 40)
        
        # Use provided values or prompt for them
        if not self.project_name:
            self.project_name = input("Project name (for namespace): ").strip()
            if not self.project_name:
                self.project_name = "external"
        else:
            print(f"✅ Project name: {self.project_name}")
            
        if not self.team_name:
            self.team_name = input("Team/Organization name: ").strip()
            if not self.team_name:
                self.team_name = "external-team"
        else:
            print(f"✅ Team name: {self.team_name}")
            
        if not self.user_email:
            self.user_email = input("Your email address: ").strip()
            if not self.user_email:
                self.user_email = "user@example.com"
        else:
            print(f"✅ User email: {self.user_email}")
            
        print(f"✅ Project name: {self.project_name}")
        print(f"✅ Team name: {self.team_name}")
        print(f"✅ User email: {self.user_email}")
        print()
        
    def check_dependencies(self):
        """Check and install required dependencies."""
        print("🔧 Checking Dependencies")
        print("-" * 40)
        
        dependencies = {
            'curl': 'curl',
            'jq': 'jq',
            'make': 'make'
        }
        
        missing = []
        for dep, package in dependencies.items():
            try:
                subprocess.run([dep, '--version'], capture_output=True, check=True)
                print(f"✅ {dep} - installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"❌ {dep} - missing")
                missing.append((dep, package))
                
        if missing:
            print("\n📦 Installing missing dependencies...")
            for dep, package in missing:
                if dep == 'jq':
                    try:
                        subprocess.run(['brew', 'install', 'jq'], check=True)
                        print(f"✅ Installed {dep}")
                    except subprocess.CalledProcessError:
                        print(f"❌ Failed to install {dep}. Please install manually:")
                        print(f"   brew install {package}")
                        return False
                else:
                    print(f"❌ Please install {dep} manually")
                    return False
        else:
            print("✅ All dependencies are installed!")
            
        print()
        return True
        
    def test_api_connection(self):
        """Test connection to the API."""
        print("🔌 Testing API Connection")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                ['curl', '-s', f'{self.api_base}/health'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ API connection successful: {self.api_base}")
                return True
            else:
                print(f"❌ API connection failed: {self.api_base}")
                print("   Make sure the AI-IDE-API is running")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ API connection timeout: {self.api_base}")
            return False
        except Exception as e:
            print(f"❌ API connection error: {e}")
            return False
            
    def initialize_onboarding(self):
        """Initialize onboarding and get API token automatically."""
        print("🚀 Initializing Onboarding")
        print("-" * 40)
        
        try:
            # Call onboarding/init endpoint
            init_payload = {
                "project_name": self.project_name,
                "team_name": self.team_name,
                "user": self.user_email,
                "journey": "external_project"
            }
            
            result = subprocess.run([
                'curl', '-s', '-X', 'POST',
                f'{self.api_base}/onboarding/init',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(init_payload)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                
                # Extract project info first (always available)
                self.project_id = response_data.get('project_id')
                self.team_id = response_data.get('team_id')
                
                print(f"✅ Project ID: {self.project_id}")
                print(f"✅ Team ID: {self.team_id}")
                
                # Extract token if available
                if 'token' in response_data:
                    self.token = response_data['token']
                    print("✅ API token generated automatically")
                    
                    # Save token
                    with open('.apitoken', 'w') as f:
                        f.write(self.token)
                        
                    print("✅ Token saved to .apitoken")
                    print()
                    return True
                else:
                    # For non-test paths, we need to generate a token separately
                    print("⚠️  No token returned from onboarding/init")
                    print("   This is normal for production paths")
                    return self.generate_api_token_manually()
                
            else:
                print(f"❌ Onboarding initialization failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Onboarding initialization error: {e}")
            return False
            
    def generate_api_token_manually(self):
        """Generate API token manually if not provided by onboarding/init."""
        print("🔑 Generating API Token")
        print("-" * 40)
        
        try:
            # Call admin/generate-token endpoint
            token_payload = {
                "description": f"First user token for {self.project_name}",
                "role": "user",
                "project_id": self.project_id,
                "user": self.user_email
            }
            
            result = subprocess.run([
                'curl', '-s', '-X', 'POST',
                f'{self.api_base}/admin/generate-token',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(token_payload)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    self.token = response_data.get('token')
                    
                    if self.token:
                        print("✅ API token generated successfully")
                        print(f"   Token: {self.token[:8]}...")
                        
                        # Save token
                        with open('.apitoken', 'w') as f:
                            f.write(self.token)
                            
                        print("✅ Token saved to .apitoken")
                        print()
                        return True
                    else:
                        print("❌ No token in response")
                        print(f"   Response: {result.stdout}")
                        return False
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {e}")
                    print(f"   Response: {result.stdout}")
                    return False
            else:
                print(f"❌ Token generation failed: {result.stderr}")
                print(f"   Response: {result.stdout}")
                return False
                
        except Exception as e:
            print(f"❌ Token generation error: {e}")
            return False
            
    def test_authentication(self):
        """Test the API token."""
        print("🔐 Testing Authentication")
        print("-" * 40)
        
        try:
            result = subprocess.run([
                'curl', '-s', '-H', f'Authorization: Bearer {self.token}',
                f'{self.api_base}/health'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Authentication successful!")
                return True
            else:
                print("❌ Authentication failed")
                print("   Please check your API token")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
            
    def generate_makefile(self):
        """Generate the external Makefile."""
        print("📝 Generating External Makefile")
        print("-" * 40)
        
        try:
            # Import the makefile generator
            sys.path.append('scripts')
            from generate_external_makefile import generate_makefile, generate_readme
            
            # Generate Makefile
            makefile_content = generate_makefile(self.api_base, self.memory_api_base, "Makefile.external")
            with open("Makefile.external", "w") as f:
                f.write(makefile_content)
            
            # Create simple usage guide
            usage_guide = f"""# AI-IDE-API External Project Setup

## Quick Start

1. **Test your connection:**
   ```bash
   make -f Makefile.external test-connection
   ```

2. **Check LLM access:**
   ```bash
   make -f Makefile.external check-llm-access
   ```

3. **Request LLM access if needed:**
   ```bash
   make -f Makefile.external request-llm-access
   ```

4. **Start using the API:**
   ```bash
   make -f Makefile.external help
   ```

## Configuration

- API Base: {self.api_base}
- Project: {self.project_name}
- Token: Stored in `.apitoken` file

## Available Commands

- `test-connection` - Test API connection and authentication
- `check-llm-access` - Check if project has LLM access enabled  
- `request-llm-access` - Show instructions for requesting LLM access
- `health` - Check API health status
- `help` - Show all available commands

## Support

For additional operations, use the API directly or contact the administrator.
"""
            
            with open("USAGE.md", "w") as f:
                f.write(usage_guide)
            
            print("✅ Generated Makefile.external")
            print("✅ Generated USAGE.md")
            print()
            return True
            
        except ImportError:
            print("❌ Could not import makefile generator")
            print("   Make sure scripts/generate_external_makefile.py exists")
            return False
        except Exception as e:
            print(f"❌ Error generating files: {e}")
            return False
            
    def create_example_files(self):
        """Create example files for testing."""
        print("📄 Creating Example Files")
        print("-" * 40)
        
        # Example memory content
        example_memory = f"""# Example Memory for {self.project_name}

This is an example memory node created during onboarding.

## Project Details
- Project: {self.project_name}
- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Type: Onboarding Example

## Content
This memory demonstrates how to create and store information in the AI-IDE-API system.
You can search for this content later using the memory-search command.

## Usage Examples
- Search: make memory-search QUERY="onboarding example"
- List namespaces: make memory-list
- View nodes: make memory-nodes NAMESPACE={self.project_name}
"""
        
        # Example rule
        example_rule = f"""# Example Rule for {self.project_name}

## Rule: External User Best Practices

### Description
This rule provides guidance for external users of the AI-IDE-API system.

### Requirements
- Always use the provided Makefile for API interactions
- Keep API tokens secure and never commit them to version control
- Use meaningful namespaces for memory organization
- Test connections before running complex operations

### Examples
```bash
# Test connection
make -f Makefile.external test-connection

# Search memories
make -f Makefile.external memory-search QUERY="your search term"

# Create memory
make -f Makefile.external memory-create FILE=content.txt NAMESPACE={self.project_name}
```

### References
- README.external.md for detailed documentation
- API health endpoint for connection testing
- Memory namespaces for organization
"""
        
        # Write files
        with open("example_memory.txt", "w") as f:
            f.write(example_memory)
            
        with open("example_rule.mdc", "w") as f:
            f.write(example_rule)
            
        print("✅ Created example_memory.txt")
        print("✅ Created example_rule.mdc")
        print()
        
    def run_initial_tests(self):
        """Run initial tests to verify setup."""
        print("🧪 Running Initial Tests")
        print("-" * 40)
        
        tests = [
            ("Connection Test", ["make", "-f", "Makefile.external", "test-connection"]),
            ("Memory API Test", ["make", "-f", "Makefile.external", "test-memory"]),
            ("Rules API Test", ["make", "-f", "Makefile.external", "test-rules"]),
        ]
        
        results = []
        for test_name, command in tests:
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"✅ {test_name} - passed")
                    results.append(True)
                else:
                    print(f"❌ {test_name} - failed")
                    results.append(False)
            except Exception as e:
                print(f"❌ {test_name} - error: {e}")
                results.append(False)
                
        print()
        return all(results)
        
    def create_example_workflow(self):
        """Create and run an example workflow."""
        print("🔄 Running Example Workflow")
        print("-" * 40)
        
        try:
            # Create memory
            print("📝 Creating example memory...")
            subprocess.run([
                "make", "-f", "Makefile.external", "memory-create",
                f"FILE=example_memory.txt", f"NAMESPACE={self.project_name}"
            ], check=True)
            
            # Search for it
            print("🔍 Searching for example memory...")
            subprocess.run([
                "make", "-f", "Makefile.external", "memory-search",
                "QUERY=onboarding example"
            ], check=True)
            
            # Propose rule
            print("📋 Proposing example rule...")
            subprocess.run([
                "make", "-f", "Makefile.external", "rule-propose",
                "FILE=example_rule.mdc"
            ], check=True)
            
            print("✅ Example workflow completed successfully!")
            print()
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Example workflow failed: {e}")
            print("   This is normal if the API is not fully configured")
            print()
            return False
            
    def show_next_steps(self):
        """Show next steps for the user."""
        print("🎯 Next Steps")
        print("-" * 40)
        print("Congratulations! Your AI-IDE-API external setup is complete.")
        print()
        print("📚 Documentation:")
        print("  - README.external.md - Complete usage guide")
        print("  - Makefile.external - All available commands")
        print()
        print("🚀 Quick Start Commands:")
        print("  make -f Makefile.external help                    # Show all commands")
        print("  make -f Makefile.external memory-search QUERY='your query'")
        print("  make -f Makefile.external memory-create FILE=content.txt NAMESPACE=myproject")
        print("  make -f Makefile.external rule-list              # List all rules")
        print("  make -f Makefile.external git-history SINCE='1 week ago'")
        print()
        print("🔧 Configuration:")
        print("  - API_BASE: {self.api_base}")
        print("  - MEMORY_API_BASE: {self.memory_api_base}")
        print("  - API_TOKEN: Stored in .apitoken file")
        print()
        print("📞 Support:")
        print("  - Check README.external.md for detailed documentation")
        print("  - Use 'make -f Makefile.external help' for command reference")
        print("  - Test connections with 'make -f Makefile.external test-connection'")
        print()
        print("=" * 80)
        print("🏴‍☠️  Happy coding with AI-IDE-API!")
        print("=" * 80)
        
    def run_onboarding(self):
        """Run the complete onboarding process."""
        self.print_banner()
        
        # Get project info
        self.get_project_info()
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Dependency check failed. Please install missing dependencies.")
            return False
            
        # Test API connection
        if not self.test_api_connection():
            print("❌ API connection failed. Please ensure the AI-IDE-API is running.")
            return False
            
        # Initialize onboarding
        if not self.initialize_onboarding():
            print("❌ Onboarding initialization failed.")
            return False
            
        # Test authentication
        if not self.test_authentication():
            print("❌ Authentication test failed.")
            return False
            
        # Generate Makefile
        if not self.generate_makefile():
            print("❌ Makefile generation failed.")
            return False
            
        # Create example files
        self.create_example_files()
        
        # Run initial tests
        self.run_initial_tests()
        
        # Run example workflow
        self.create_example_workflow()
        
        # Show next steps
        self.show_next_steps()
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Updated external onboarding for AI-IDE-API")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="API base URL")
    parser.add_argument("--memory-api-base", default=DEFAULT_MEMORY_API_BASE, help="Memory API base URL")
    parser.add_argument("--project", help="Project name (for namespace)")
    parser.add_argument("--team", help="Team/Organization name")
    parser.add_argument("--user", help="User email address")
    parser.add_argument("--token", help="API token (will generate automatically if not provided)")
    
    args = parser.parse_args()
    
    # Create onboarding instance
    onboarding = ExternalOnboarding(args.api_base, args.memory_api_base)
    
    # Set project info if provided
    if args.project:
        onboarding.project_name = args.project
    if args.team:
        onboarding.team_name = args.team
    if args.user:
        onboarding.user_email = args.user
        
    # Set token if provided (skip automatic generation)
    if args.token:
        onboarding.token = args.token
        with open('.apitoken', 'w') as f:
            f.write(args.token)
    
    # Run onboarding
    success = onboarding.run_onboarding()
    
    if success:
        print("\n🎉 Onboarding completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Onboarding failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 
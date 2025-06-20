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
        
        self.project_name = input("Project name (for namespace): ").strip()
        if not self.project_name:
            self.project_name = "external"
            
        print(f"✅ Project name: {self.project_name}")
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
            
    def get_api_token(self):
        """Get API token from user."""
        print("🔑 API Authentication")
        print("-" * 40)
        
        # Check if token file exists
        if os.path.exists('.apitoken'):
            with open('.apitoken', 'r') as f:
                existing_token = f.read().strip()
            if existing_token:
                use_existing = input(f"Found existing token: {existing_token[:8]}... Use it? (y/n): ").lower()
                if use_existing == 'y':
                    self.token = existing_token
                    print("✅ Using existing token")
                    print()
                    return True
                    
        # Get new token
        print("Please provide your API token:")
        print("(You can get this from the AI-IDE-API admin interface)")
        self.token = input("API Token: ").strip()
        
        if not self.token:
            print("❌ No token provided")
            return False
            
        # Save token
        with open('.apitoken', 'w') as f:
            f.write(self.token)
            
        print("✅ Token saved to .apitoken")
        print()
        return True
        
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
                
            # Generate README
            readme_content = generate_readme(self.api_base, self.memory_api_base)
            with open("README.external.md", "w") as f:
                f.write(readme_content)
                
            print("✅ Generated Makefile.external")
            print("✅ Generated README.external.md")
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
            
        # Get and test authentication
        if not self.get_api_token():
            print("❌ Authentication setup failed.")
            return False
            
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
    parser.add_argument("--token", help="API token (will prompt if not provided)")
    
    args = parser.parse_args()
    
    # Create onboarding instance
    onboarding = ExternalOnboarding(args.api_base, args.memory_api_base)
    
    # Set project name if provided
    if args.project:
        onboarding.project_name = args.project
        
    # Set token if provided
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
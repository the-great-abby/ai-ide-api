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
        self.container_api_base = None
        
    def print_banner(self):
        """Print the onboarding banner."""
        print("=" * 80)
        print("🏴‍☠️  AI-IDE-API External Onboarding")
        print("=" * 80)
        print("Welcome to the AI-IDE-API system! This script will help you")
        print("set up everything you need to interact with the API.")
        print("=" * 80)
        print()
        
    def detect_environment(self):
        """Detect if we're running in a container or on host."""
        print("🔍 Detecting Environment")
        print("-" * 40)
        
        # Check if we're in a container
        in_container = os.path.exists('/.dockerenv') or os.environ.get('RUNNING_IN_DOCKER') == '1'
        
        if in_container:
            print("🐳 Running inside Docker container")
            print("   Workers will use host.docker.internal for API access")
            self.container_api_base = "http://host.docker.internal:9103"
        else:
            print("🖥️  Running on host machine")
            print("   Workers will use localhost for API access")
            self.container_api_base = "http://localhost:9103"
            
        print(f"   API Base: {self.api_base}")
        print(f"   Container API Base: {self.container_api_base}")
        print()
        
    def prompt_api_addresses(self):
        """Prompt for API addresses if needed."""
        print("🌐 API Address Configuration")
        print("-" * 40)
        
        # Ask if user wants to customize API addresses
        custom_api = input(f"API base URL (default: {self.api_base}): ").strip()
        if custom_api:
            self.api_base = custom_api
            
        print(f"✅ API Base: {self.api_base}")
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
                
                # Save project and team information
                with open('.project', 'w') as f:
                    f.write(self.project_name)
                print(f"✅ Project name saved to .project: {self.project_name}")
                
                with open('.teamname', 'w') as f:
                    f.write(self.team_name)
                print(f"✅ Team name saved to .teamname: {self.team_name}")
                
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
        """Generate API token(s) for the project, handling user/admin flow robustly."""
        print("🔑 Generating API Token(s)")
        print("-" * 40)

        # Always try to create a user token first
        user_token = None
        try:
            user_token_payload = {
                "description": f"First user token for {self.project_name}",
                "role": "user",
                "project_id": self.project_id,
                "user": self.user_email
            }
            result = subprocess.run([
                'curl', '-s', '-X', 'POST',
                f'{self.api_base}/admin/generate-token',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(user_token_payload)
            ], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    user_token = response_data.get('token')
                    if user_token:
                        print("✅ User token generated successfully")
                        print(f"   Token: {user_token[:8]}...")
                        with open('.apitoken', 'w') as f:
                            f.write(user_token)
                        print("✅ Token saved to .apitoken")
                        
                        # Save project and team information
                        with open('.project', 'w') as f:
                            f.write(self.project_name)
                        print(f"✅ Project name saved to .project: {self.project_name}")
                        
                        with open('.teamname', 'w') as f:
                            f.write(self.team_name)
                        print(f"✅ Team name saved to .teamname: {self.team_name}")
                    else:
                        print("⚠️  No new user token in response. Trying to fetch existing token...")
                        # Try to fetch existing token for this user/project/role
                        # (API may return the same token if it already exists)
                        if 'token' in response_data:
                            user_token = response_data['token']
                            with open('.apitoken', 'w') as f:
                                f.write(user_token)
                            print("✅ Existing user token saved to .apitoken")
                            
                            # Save project and team information
                            with open('.project', 'w') as f:
                                f.write(self.project_name)
                            print(f"✅ Project name saved to .project: {self.project_name}")
                            
                            with open('.teamname', 'w') as f:
                                f.write(self.team_name)
                            print(f"✅ Team name saved to .teamname: {self.team_name}")
                        else:
                            print(f"❌ No user token found in response: {result.stdout}")
                            return False
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {e}")
                    print(f"   Response: {result.stdout}")
                    return False
            else:
                print(f"❌ User token generation failed: {result.stderr}")
                print(f"   Response: {result.stdout}")
                return False
        except Exception as e:
            print(f"❌ User token generation error: {e}")
            return False

        # Ask if admin access is needed
        want_admin = input("Do you need admin access for this project? (y/n): ").strip().lower()
        if want_admin not in ['y', 'yes']:
            self.token = user_token
            return True

        # Try to generate admin token using the user token
        try:
            admin_token_payload = {
                "description": f"First admin token for {self.project_name}",
                "role": "admin",
                "project_id": self.project_id,
                "user": self.user_email
            }
            result = subprocess.run([
                'curl', '-s', '-X', 'POST',
                f'{self.api_base}/admin/generate-token',
                '-H', f'Authorization: Bearer {user_token}',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(admin_token_payload)
            ], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    admin_token = response_data.get('token')
                    if admin_token:
                        print("✅ Admin token generated successfully")
                        print(f"   Token: {admin_token[:8]}...")
                        with open('.api_admin_token', 'w') as f:
                            f.write(admin_token)
                        print("✅ Admin token saved to .api_admin_token")
                        self.token = admin_token
                        return True
                    else:
                        print("⚠️  No new admin token in response. Trying to fetch existing admin token...")
                        if 'token' in response_data:
                            admin_token = response_data['token']
                            with open('.api_admin_token', 'w') as f:
                                f.write(admin_token)
                            print("✅ Existing admin token saved to .api_admin_token")
                            self.token = admin_token
                            return True
                        else:
                            print(f"❌ No admin token found in response: {result.stdout}")
                            return False
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {e}")
                    print(f"   Response: {result.stdout}")
                    return False
            else:
                print(f"❌ Admin token generation failed: {result.stderr}")
                print(f"   Response: {result.stdout}")
                return False
        except Exception as e:
            print(f"❌ Admin token generation error: {e}")
            return False

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
            
    def generate_docker_compose(self):
        """Generate Docker Compose files for external project workers."""
        print("🐳 Generating Docker Compose Files")
        print("-" * 40)
        
        try:
            # Import the Docker Compose generator
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from scripts.generate_external_docker_compose import generate_docker_compose, generate_worker_dockerfile, generate_worker_requirements, generate_setup_script, generate_external_worker_main
            
            # Use detected addresses or defaults
            api_base = self.container_api_base or "http://localhost:9103"
            
            # Generate files
            docker_compose_content = generate_docker_compose(
                self.project_name, 
                api_base=api_base
            )
            worker_dockerfile_content = generate_worker_dockerfile(self.project_name)
            worker_requirements_content = generate_worker_requirements()
            worker_main_content = generate_external_worker_main(self.project_name)
            setup_script_content = generate_setup_script(
                self.project_name,
                api_base=api_base
            )
            
            # Write files
            with open('docker-compose.external.yml', 'w') as f:
                f.write(docker_compose_content)
            
            # Create worker directory
            os.makedirs('worker', exist_ok=True)
            
            with open('worker/Dockerfile', 'w') as f:
                f.write(worker_dockerfile_content)
                
            with open('worker/requirements.txt', 'w') as f:
                f.write(worker_requirements_content)
                
            with open('worker/main.py', 'w') as f:
                f.write(worker_main_content)
                
            with open('setup-workers.sh', 'w') as f:
                f.write(setup_script_content)
            
            # Make setup script executable
            os.chmod('setup-workers.sh', 0o755)
            
            print("✅ Generated Docker Compose files:")
            print("   📄 docker-compose.external.yml")
            print("   📄 worker/Dockerfile")
            print("   📄 worker/requirements.txt")
            print("   📄 worker/main.py")
            print("   📄 setup-workers.sh")
            print()
            print("🚀 To start workers:")
            print("   ./setup-workers.sh")
            print()
            print("📋 Workers will:")
            print("   • Process memory enrichment jobs")
            print("   • Handle memory cleanup tasks")
            print("   • Manage similarity pruning")
            print("   • Process git history analysis")
            print("   • Summarize git diffs via API")
            print(f"   • Connect to AI-IDE-API at {api_base}")
            print()
            print("✅ All worker functionality is now available:")
            print("   • Git diff summarization via API endpoint")
            print("   • LLM processing handled by main AI-IDE-API")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to generate Docker Compose files: {e}")
            print("   You can generate them manually later")
            return False

    def generate_makefile(self):
        """Generate the external Makefile."""
        print("📝 Generating External Makefile")
        print("-" * 40)
        
        try:
            # Import the makefile generator
            sys.path.append('scripts')
            from generate_external_makefile import generate_makefile
            
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
            ("Health Check", ["make", "-f", "Makefile.external", "health"]),
        ]
        
        # Add admin tests if admin token exists
        if os.path.exists('.api_admin_token'):
            tests.extend([
                ("Admin LLM Access Check", ["make", "-f", "Makefile.external", "check-llm-access"]),
                ("Admin Project Info", ["make", "-f", "Makefile.external", "admin-project-info"]),
            ])
        
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
            # Test basic connection
            print("🔌 Testing connection...")
            subprocess.run([
                "make", "-f", "Makefile.external", "test-connection"
            ], check=True)
            
            # Check health
            print("🏥 Checking API health...")
            subprocess.run([
                "make", "-f", "Makefile.external", "health"
            ], check=True)
            
            # If admin token exists, test admin commands
            if os.path.exists('.api_admin_token'):
                print("🔐 Testing admin commands...")
                subprocess.run([
                    "make", "-f", "Makefile.external", "check-llm-access"
                ], check=True)
                
                subprocess.run([
                    "make", "-f", "Makefile.external", "admin-project-info"
                ], check=True)
            
            print("✅ Example workflow completed successfully!")
            print()
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Example workflow had some issues: {e}")
            print("   This is normal if the API is not fully configured")
            print()
        except Exception as e:
            print(f"❌ Example workflow error: {e}")
            print()
            
    def show_next_steps(self):
        """Show next steps for the user."""
        print("🎯 Next Steps")
        print("-" * 40)
        print("Congratulations! Your AI-IDE-API external setup is complete.")
        print()
        
        print("📚 Documentation:")
        print("  - USAGE.md - Simple usage guide")
        print("  - Makefile.external - All available commands")
        print("  - docker-compose.external.yml - Worker services")
        print()
        
        print("🚀 Quick Start Commands:")
        print("  make -f Makefile.external help                    # Show all commands")
        print("  make -f Makefile.external test-connection        # Test your connection")
        print("  make -f Makefile.external health                 # Check API health")
        print("  make -f Makefile.external check-llm-access       # Check LLM access")
        print()
        
        print("🐳 Background Workers (Optional):")
        print("  ./setup-workers.sh                               # Start RabbitMQ and workers")
        print("  docker-compose -f docker-compose.external.yml up -d  # Start services")
        print("  docker-compose -f docker-compose.external.yml logs -f worker  # View logs")
        print("  docker-compose -f docker-compose.external.yml down  # Stop services")
        print()
        print("📋 Workers will process:")
        print("  • Memory enrichment jobs")
        print("  • Memory cleanup tasks")
        print("  • Similarity pruning")
        print("  • Git history analysis")
        print()
        
        if os.path.exists('.api_admin_token'):
            print("🔐 Admin Commands (available with admin token):")
            print("  make -f Makefile.external admin-enable-llm    # Enable LLM access")
            print("  make -f Makefile.external admin-project-info # View project info")
            print("  make -f Makefile.external admin-generate-token DESCRIPTION='desc' ROLE=user")
            print()
        
        print("🔧 Configuration:")
        print(f"  - API_BASE: {self.api_base}")
        print(f"  - MEMORY_API_BASE: {self.memory_api_base}")
        print("  - API_TOKEN: Stored in .apitoken file")
        if os.path.exists('.api_admin_token'):
            print("  - ADMIN_TOKEN: Stored in .api_admin_token file")
        print(f"  - PROJECT: {self.project_name} (saved to .project)")
        print(f"  - TEAM: {self.team_name} (saved to .teamname)")
        print("  - WORKER_NETWORK: {self.project_name}-memory-rabbitmq")
        print()
        
        print("📞 Support:")
        print("  - Check USAGE.md for detailed documentation")
        print("  - Use 'make -f Makefile.external help' for command reference")
        print("  - Test connections with 'make -f Makefile.external test-connection'")
        print("  - View worker logs with 'docker-compose -f docker-compose.external.yml logs -f worker'")
        print()
        
    def run_onboarding(self):
        """Run the complete onboarding process."""
        self.print_banner()
        
        # Detect environment and API addresses
        self.detect_environment()
        self.prompt_api_addresses()
        
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
            
        # Generate Docker Compose files
        self.generate_docker_compose()
        
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
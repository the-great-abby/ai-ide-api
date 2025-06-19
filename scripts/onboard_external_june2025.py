#!/usr/bin/env python3
"""
External Onboarding Script (June 2025)
Python version of the external onboarding script with enhanced features.
"""

import requests
import json
import os
import sys
from typing import Optional, Dict, Any


def get_user_input(prompt: str, default: Optional[str] = None) -> str:
    """Get user input with optional default value."""
    if default:
        prompt = f"{prompt} (default: {default}): "
    else:
        prompt = f"{prompt}: "

    while True:
        try:
            value = input(prompt).strip()
            if not value and default:
                return default
            if value:
                return value
            print("Please provide a value.")
        except KeyboardInterrupt:
            print("\nOnboarding cancelled.")
            sys.exit(1)


def test_api_connectivity(api_url: str) -> bool:
    """Test if the API is accessible."""
    try:
        response = requests.get(f"{api_url}/docs", timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ API connectivity test failed: {e}")
        return False


def generate_token(api_url: str, project_name: str, user: str) -> Optional[str]:
    """Generate an API token for the external project."""
    try:
        payload = {
            "description": f"Token for {project_name}",
            "role": "user",
            "user": user,
        }

        response = requests.post(
            f"{api_url}/admin/generate-token",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("token")
        else:
            print(
                f"❌ Token generation failed: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        print(f"❌ Error generating token: {e}")
        return None


def initialize_onboarding(
    api_url: str, project_name: str, onboarding_path: str, user: str
) -> bool:
    """Initialize onboarding for the external project."""
    try:
        payload = {
            "project_name": project_name,
            "journey": onboarding_path,
            "user": user,
        }

        response = requests.post(
            f"{api_url}/onboarding/init",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 200:
            print(f"✅ Onboarding initialized: {response.json().get('buddy_intro','')}")
            return True
        else:
            print(
                f"❌ Onboarding initialization failed: {response.status_code} - {response.text}"
            )
            return False

    except Exception as e:
        print(f"❌ Error initializing onboarding: {e}")
        return False


def test_memory_api(api_url: str, token: str) -> bool:
    """Test the memory API with a simple operation."""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # Test payload
        payload = {
            "namespace": "onboarding_test",
            "content": "Test memory node from external onboarding script",
            "meta": json.dumps(
                {"tags": ["onboarding", "test"], "source": "external_script"}
            ),
        }

        response = requests.post(
            f"{api_url}/memory/nodes", json=payload, headers=headers, timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(
                f"✅ Memory API test successful - created node: {result.get('id', 'unknown')}"
            )
            return True
        else:
            print(f"❌ Memory API test failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing memory API: {e}")
        return False


def save_token_to_file(token: str, filename: str = ".apitoken") -> bool:
    """Save the API token to a file."""
    try:
        with open(filename, "w") as f:
            f.write(token)
        print(f"✅ Token saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving token: {e}")
        return False


def create_env_file(api_url: str, token: str, project_name: str) -> bool:
    """Create a .env file with configuration."""
    try:
        env_content = f"""# AI IDE API Configuration
AI_IDE_API_URL={api_url}
MEMORY_API_URL={api_url}/memory
MEMORY_API_TOKEN={token}

# Project Configuration
PROJECT_NAME={project_name}

# RabbitMQ Configuration (if using workers)
RABBITMQ_URL=amqp://user:password@localhost:5672/

# Worker Configuration
WORKER_LOG_LEVEL=INFO
WORKER_MAX_RETRIES=3
"""

        with open(".env", "w") as f:
            f.write(env_content)

        print("✅ Created .env file with configuration")
        return True

    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False


def main():
    """Main onboarding flow."""
    print("🏴‍☠️  AI IDE External Onboarding Script (June 2025)")
    print("=" * 50)

    # Get configuration from user
    api_url = get_user_input("Enter the API base URL", "http://localhost:9103")
    api_url = api_url.rstrip("/")

    project_name = get_user_input("Enter your project name")
    user = get_user_input("Enter user identifier (email or username)")
    onboarding_path = get_user_input("Enter onboarding path", "external_project")

    print(f"\n🔍 Testing API connectivity...")
    if not test_api_connectivity(api_url):
        print("❌ Cannot connect to API. Please check the URL and try again.")
        sys.exit(1)

    print("✅ API is accessible!")

    print(f"\n🔑 Generating API token...")
    token = generate_token(api_url, project_name, user)
    if not token:
        print("❌ Failed to generate token. Please check your API access.")
        sys.exit(1)

    print(f"✅ Token generated: {token[:8]}...")

    print(f"\n📝 Initializing onboarding...")
    if not initialize_onboarding(api_url, project_name, onboarding_path, user):
        print("❌ Failed to initialize onboarding.")
        sys.exit(1)

    print("✅ Onboarding initialized!")

    print(f"\n🧪 Testing memory API...")
    if not test_memory_api(api_url, token):
        print("⚠️  Memory API test failed, but continuing...")

    print(f"\n💾 Saving configuration...")
    if not save_token_to_file(token):
        print("❌ Failed to save token.")
        sys.exit(1)

    if not create_env_file(api_url, token, project_name):
        print("⚠️  Failed to create .env file, but continuing...")

    print(f"\n🎉 Onboarding completed successfully!")
    print("=" * 50)
    print("Next steps:")
    print(f"1. Your API token is saved in .apitoken")
    print(f"2. Configuration is saved in .env")
    print(f"3. Explore the API docs at {api_url}/docs")
    print(f"4. Follow the onboarding steps for '{onboarding_path}'")
    print(f"5. Use 'Authorization: Bearer <token>' in your API requests")
    print("\nExample API call:")
    print(f"curl -X GET {api_url}/memory/nodes \\")
    print(f"  -H 'Authorization: Bearer {token[:8]}...'")
    print("\nHappy coding! 🚀")


if __name__ == "__main__":
    main()

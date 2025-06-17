#!/usr/bin/env python3
"""
External Onboarding Script
This script can be downloaded from the API for easy onboarding.
"""
import requests
import json
import os
import sys

ONBOARDING_PATHS_FILE = os.path.join(os.path.dirname(__file__), '../onboarding_paths.json')

# Load onboarding paths
try:
    with open(ONBOARDING_PATHS_FILE) as f:
        onboarding_paths = json.load(f)["paths"]
except Exception as e:
    print(f"Warning: Could not load onboarding paths: {e}")
    onboarding_paths = []

print("\nAvailable onboarding paths:")
for path in onboarding_paths:
    display = path.get("display_name") or path.get("title") or path["name"]
    print(f"- {path['name']}: {display}")

# --- Improved API base URL prompt ---
print("\nEnter the API base URL:")
print("  - If running inside a dev container:      http://api:8000")
print("  - If running on your host machine:        http://localhost:9103")
print("  - If running in Docker but want to reach the host: http://host.docker.internal:9103")

# Try to auto-detect environment
api_url_default = "http://localhost:9103"
try:
    # Check for RUNNING_IN_DOCKER env var
    if os.environ.get("RUNNING_IN_DOCKER") == "1":
        api_url_default = "http://api:8000"
    else:
        # Check cgroup for docker
        with open("/proc/1/cgroup", "rt") as f:
            cgroup_content = f.read()
        if "docker" in cgroup_content or "containerd" in cgroup_content:
            api_url_default = "http://api:8000"
except Exception:
    pass

# If on Mac/Windows and want to reach host, user can use host.docker.internal
# (We don't auto-detect this, just show as an option)

api_url_input = input(f"API base URL [{api_url_default}]: ").strip()
API_URL = api_url_input if api_url_input else api_url_default

PROJECT_NAME = input("Enter your project name: ").strip()
print("Enter onboarding path from the list above:")
ONBOARDING_PATH = input("Onboarding path: ").strip()

# Step 1: Generate user token
print("\nGenerating user token...")
token_resp = requests.post(f"{API_URL}/admin/generate-token", json={"description": f"Token for {PROJECT_NAME}", "role": "user"})
if token_resp.status_code != 200:
    print(f"Error generating token: {token_resp.status_code} {token_resp.text}")
    exit(1)
token = token_resp.json()["token"]
print(f"Token generated: {token[:6]}... (saved to .apitoken)")
with open(".apitoken", "w") as f:
    f.write(token)

# After generating the token, write it to /code/.apitoken
try:
    with open("/code/.apitoken", "w") as f:
        f.write(token)
    print("Token also saved to /code/.apitoken")
except Exception as e:
    print(f"Warning: Could not write token to /code/.apitoken: {e}")

# Step 2: Register project and onboarding path
print("\nInitializing onboarding journey...")
init_resp = requests.post(f"{API_URL}/onboarding/init", json={"project_name": PROJECT_NAME, "path": ONBOARDING_PATH}, headers={"Authorization": f"Bearer {token}"})
if init_resp.status_code != 200:
    print(f"Error initializing onboarding: {init_resp.status_code} {init_resp.text}")
    exit(1)
print("Onboarding initialized successfully!")
print(f"Response: {init_resp.json()}")

print("\nNext steps:")
print(f"- Your API token is saved in .apitoken. Use it as 'Authorization: Bearer <token>' in requests.")
print(f"- Explore the API docs at {API_URL}/docs")
print(f"- Follow the onboarding steps for '{ONBOARDING_PATH}' in the docs or via the API.") 
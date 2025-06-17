#!/usr/bin/env python3
"""
INTERNAL USE ONLY: This script is now used for internal developer onboarding.
External users should use the new onboarding script: onboard_external_june2025.py
(Downloadable from the API at /scripts/onboard_external.py)
"""
import requests
import json
import os
import sys
import subprocess

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

# Prompt for project and team name
PROJECT_NAME = input("Enter your project name: ").strip()
TEAM_NAME = input("Enter your team name: ").strip()
print("Enter onboarding path from the list above:")
ONBOARDING_PATH = input("Onboarding path: ").strip()

# Step 1: Initialize onboarding journey (create/get project and team)
print("\nInitializing onboarding journey...")
init_payload = {"project_name": PROJECT_NAME, "team_name": TEAM_NAME, "path": ONBOARDING_PATH}
init_resp = requests.post(f"{API_URL}/onboarding/init", json=init_payload)
if init_resp.status_code != 200:
    print(f"Error initializing onboarding: {init_resp.status_code} {init_resp.text}")
    exit(1)
init_json = init_resp.json()
print("Onboarding initialized successfully!")
print(f"Response: {init_json}")
# Save the full onboarding response for later reference
api_info_capture_path = "/code/.api_info_capture"
with open(api_info_capture_path, "w") as f:
    json.dump(init_json, f, indent=2)
project_id = init_json.get("project_id")
if not project_id:
    print("Error: onboarding/init did not return a project_id!")
    exit(1)

# Step 2: Generate user token associated with the project
print("\nGenerating user token...")
token_resp = requests.post(f"{API_URL}/admin/generate-token", json={"description": f"Token for {PROJECT_NAME}", "role": "user", "project_id": project_id})
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

# Save all key info to .api_info_capture
api_info = {
    "api_token": token,
    "project_id": project_id,
    "project_name": PROJECT_NAME,
    "team_id": init_json.get("team_id"),
    "team_name": TEAM_NAME,
}
with open(api_info_capture_path, "w") as f:
    json.dump(api_info, f, indent=2)
# Save team_name and project_name to their own files
with open("/code/.teamname", "w") as f:
    f.write(TEAM_NAME)
with open("/code/.projectname", "w") as f:
    f.write(PROJECT_NAME)

# Step 3: Grant project write permission for project_name/* namespace (requires admin token)
admin_token = None
admin_token_path = "/code/.api_admin_token"
if os.path.exists(admin_token_path):
    with open(admin_token_path) as f:
        admin_token = f.read().strip()
if not admin_token and os.path.exists(".api_admin_token"):
    with open(".api_admin_token") as f:
        admin_token = f.read().strip()
if admin_token:
    namespace_pattern = f"{PROJECT_NAME}/*"
    print(f"\n[onboard_external] Granting write permission for namespace pattern: {namespace_pattern}")
    perm_payload = {
        "namespace": namespace_pattern,
        "permission_type": "write",
        "project_id": project_id
    }
    perm_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    perm_resp = requests.post(f"{API_URL}/memory/admin/namespace-permissions", headers=perm_headers, json=perm_payload)
    if perm_resp.status_code == 200:
        print(f"[onboard_external] Successfully granted write permission for {namespace_pattern}")
    else:
        print(f"[onboard_external] Failed to grant write permission: {perm_resp.status_code} {perm_resp.text}")
else:
    print("[onboard_external] Warning: No admin token found. Cannot grant project-wide namespace permission automatically.")

print("\nNext steps:")
print(f"- Your API token is saved in .apitoken. Use it as 'Authorization: Bearer <token>' in requests.")
print(f"- Explore the API docs at {API_URL}/docs")
print(f"- Follow the onboarding steps for '{ONBOARDING_PATH}' in the docs or via the API.") 
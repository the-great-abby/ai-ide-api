# This script is a copy of onboard_external.py, adapted for admin onboarding automation.
# It will perform onboarding/init, generate an admin token, and save both tokens for later use.

import os
import sys
import json
import requests

# Prompt for API URL if not set in environment
api_url_env = os.environ.get("API_URL")
default_api_url = "http://api:8000"
if api_url_env:
    print(f"API_URL environment variable detected: {api_url_env}")
    API_URL = api_url_env
else:
    user_input = input(f"Enter API URL [{default_api_url}]: ").strip()
    API_URL = user_input or default_api_url

# Prompt for project and team name
PROJECT_NAME = input("Enter project name: ").strip()
TEAM_NAME = input("Enter team name: ").strip()

# Prompt for onboarding path
print("Enter onboarding path (e.g., internal_dev, external_project, ai_agent):")
ONBOARDING_PATH = input("Onboarding path: ").strip()

# Step 1: Initialize onboarding journey (create/get project and team)
print("\n[onboarding_admin] Initializing onboarding journey...")
init_payload = {"project_name": PROJECT_NAME, "team_name": TEAM_NAME, "path": ONBOARDING_PATH}
init_resp = requests.post(f"{API_URL}/onboarding/init", json=init_payload)
if init_resp.status_code != 200:
    print(f"Error initializing onboarding: {init_resp.status_code} {init_resp.text}")
    exit(1)
init_json = init_resp.json()
print("Onboarding initialized successfully!")
print(f"Response: {init_json}")

project_id = init_json.get("project_id")
if not project_id:
    print("Error: onboarding/init did not return a project_id!")
    exit(1)

# Step 2: Generate user token associated with the project
print("\n[onboarding_admin] Generating user token...")
token_resp = requests.post(f"{API_URL}/admin/generate-token", json={"description": f"Token for {PROJECT_NAME}", "role": "user", "project_id": project_id})
if token_resp.status_code != 200:
    print(f"Error generating user token: {token_resp.status_code} {token_resp.text}")
    if token_resp.status_code == 401:
        print("\n[onboarding_admin] It looks like a user token for this project already exists and an admin token is now required to generate new tokens.")
        print("Attempting to load previously saved user token from /code/.apitoken or /code/.api_info_capture...")
        user_token = None
        # Try to load from /code/.apitoken
        apitoken_path = os.path.join("/code", ".apitoken")
        if os.path.exists(apitoken_path):
            with open(apitoken_path) as f:
                user_token = f.read().strip()
        # Try to load from /code/.api_info_capture if not found
        api_info_path = os.path.join("/code", ".api_info_capture")
        if not user_token and os.path.exists(api_info_path):
            try:
                with open(api_info_path) as f:
                    info = json.load(f)
                    user_token = info.get("api_token")
            except Exception:
                pass
        if not user_token:
            print("[onboarding_admin] Could not find a previously saved user token. Please check your onboarding files or contact your admin.")
            exit(1)
        print(f"[onboarding_admin] Loaded user token: {user_token[:6]}... Proceeding to generate admin token.")
    else:
        exit(1)
else:
    user_token = token_resp.json()["token"]
    with open(os.path.join("/code", ".apitoken"), "w") as f:
        f.write(user_token)

# Step 3: Generate admin token using user token
print("\n[onboarding_admin] Generating admin token...")
admin_token_payload = {
    "description": "Admin token for LLM access",
    "role": "admin",
    "project_id": project_id
}
headers = {
    "Authorization": f"Bearer {user_token}",
    "Content-Type": "application/json"
}
admin_token_resp = requests.post(f"{API_URL}/admin/generate-token", headers=headers, json=admin_token_payload)
if admin_token_resp.status_code != 200:
    print(f"Error generating admin token: {admin_token_resp.status_code} {admin_token_resp.text}")
    exit(1)
admin_token = admin_token_resp.json()["token"]
print(f"Admin token generated: {admin_token[:6]}... (saved to .api_admin_token)")
with open(os.path.join("/code", ".api_admin_token"), "w") as f:
    f.write(admin_token)

# Step 4: Grant project write permission for project_name/* namespace
namespace_pattern = f"{PROJECT_NAME}/*"
print(f"\n[onboarding_admin] Granting write permission for namespace pattern: {namespace_pattern}")
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
    print(f"[onboarding_admin] Successfully granted write permission for {namespace_pattern}")
else:
    print(f"[onboarding_admin] Failed to grant write permission: {perm_resp.status_code} {perm_resp.text}")

# Save all key info to .api_info_capture
api_info = {
    "api_token": user_token,
    "api_admin_token": admin_token,
    "project_id": project_id,
    "project_name": PROJECT_NAME,
    "team_id": init_json.get("team_id"),
    "team_name": TEAM_NAME,
}
with open(os.path.join("/code", ".api_info_capture"), "w") as f:
    json.dump(api_info, f, indent=2)
# Save team_name and project_name to their own files
with open(os.path.join("/code", ".teamname"), "w") as f:
    f.write(TEAM_NAME)
with open(os.path.join("/code", ".projectname"), "w") as f:
    f.write(PROJECT_NAME)

print("\n[onboarding_admin] Onboarding complete!")
print(f"  Project: {PROJECT_NAME} ({project_id})")
print(f"  Team: {TEAM_NAME} ({init_json.get('team_id')})")
print(f"  User token: {user_token}")
print(f"  Admin token: {admin_token}")
print("  All info saved to .api_info_capture, .apitoken, .api_admin_token, .teamname, .projectname in /code/") 
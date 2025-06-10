#!/usr/bin/env python3
"""
External Onboarding Script
This script can be downloaded from the API for easy onboarding.
"""
import requests
import json
import os

API_URL = input("Enter the API base URL (e.g., http://localhost:9103): ").strip().rstrip('/')
PROJECT_NAME = input("Enter your project name: ").strip()
ONBOARDING_PATH = input("Enter onboarding path (e.g., external_project): ").strip()

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

# Step 2: Register project and onboarding path
print("Registering project and onboarding path...")
init_resp = requests.post(f"{API_URL}/onboarding/init", json={"project_name": PROJECT_NAME, "path": ONBOARDING_PATH})
if init_resp.status_code != 200:
    print(f"Error initializing onboarding: {init_resp.status_code} {init_resp.text}")
    exit(1)
print("Onboarding initialized!")

print("\nNext steps:")
print(f"- Your API token is saved in .apitoken. Use it as 'Authorization: Bearer <token>' in requests.")
print(f"- Explore the API docs at {API_URL}/docs")
print(f"- Follow the onboarding steps for '{ONBOARDING_PATH}' in the docs or via the API.") 
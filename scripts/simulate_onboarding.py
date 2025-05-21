import requests
import sys
import os

API_URL = os.environ.get("ONBOARDING_API_URL", "http://api:8000")


def simulate_onboarding(project_id, path):
    print(f"\n--- Simulating onboarding for project_id='{project_id}', path='{path}' ---")
    # 1. Initialize onboarding
    resp = requests.post(f"{API_URL}/onboarding/init", json={"project_id": project_id, "path": path})
    print("Init:", resp.status_code, resp.json())

    # 2. Fetch progress
    resp = requests.get(f"{API_URL}/onboarding/progress/{project_id}?path={path}")
    print("Progress:", resp.status_code)
    progress = resp.json()
    for step in progress:
        print(f"  - Step: {step['step']}, Completed: {step['completed']}")

    # 3. (Optional) Mark first step as complete
    if progress:
        step_id = progress[0]["id"]
        resp = requests.patch(f"{API_URL}/onboarding/progress/{step_id}", json={"completed": True})
        print(f"Mark complete for step '{progress[0]['step']}':", resp.status_code, resp.json())

    # 4. Fetch onboarding docs
    resp = requests.get(f"{API_URL}/onboarding-docs")
    print("Onboarding docs (first 200 chars):", resp.status_code, resp.text[:200], "...")
    resp = requests.get(f"{API_URL}/onboarding/user_story/{path}")
    print(f"User story for path '{path}' (first 200 chars):", resp.status_code, resp.text[:200], "...")


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/simulate_onboarding.py <project_id> <onboarding_path>")
        print("Example: python scripts/simulate_onboarding.py test_onboarding external_project")
        sys.exit(1)
    project_id = sys.argv[1]
    path = sys.argv[2]
    simulate_onboarding(project_id, path)

if __name__ == "__main__":
    main() 
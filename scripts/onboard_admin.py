import requests
import time
import os
import sys

API_URL = os.environ.get("API_URL", "http://localhost:9104/admin/generate-token")
LIST_URL = os.environ.get("LIST_URL", "http://localhost:9104/admin/tokens")

# --- GUARD: Prevent running against test DB/host ---
def is_test_env(url):
    return (
        "test-db" in url or
        "localhost:9104" in url and os.environ.get("ENVIRONMENT") == "test" or
        "rulesdb" in url and os.environ.get("ENVIRONMENT") == "test"
    )

if is_test_env(API_URL) or is_test_env(LIST_URL):
    print(f"[GUARD] ABORTING: onboard_admin.py detected test DB or test host in API_URL or LIST_URL!")
    print(f"  API_URL: {API_URL}")
    print(f"  LIST_URL: {LIST_URL}")
    print(f"  ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
    sys.exit(1)
else:
    print(f"[onboard_admin.py] Running with:")
    print(f"  API_URL: {API_URL}")
    print(f"  LIST_URL: {LIST_URL}")
    print(f"  ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")

# Wait for the API to be available before proceeding
def wait_for_api(url, timeout=60, interval=2):
    print(f"Waiting for API at {url} to become available...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url)
            if resp.status_code < 500:
                print("API is available!")
                return True
        except Exception:
            pass
        time.sleep(interval)
    print(f"API at {url} did not become available after {timeout} seconds.")
    return False

def onboard_admin():
    if not wait_for_api(LIST_URL):
        print("Aborting onboarding: API not available.")
        exit(1)
    # Try to list existing tokens
    try:
        resp = requests.get(LIST_URL)
        if resp.status_code == 200:
            tokens = resp.json()
            admin_tokens = [t for t in tokens if t.get("role") == "admin"]
            if admin_tokens:
                print("Existing admin token(s) found:")
                for t in admin_tokens:
                    print("  ", t.get("token", t))
                return
    except Exception as e:
        print("Warning: Could not check for existing tokens:", e)
    # If no admin token, create a normal user token first (no Authorization header)
    user_data = {"description": "Bootstrap user token", "role": "user"}
    user_resp = requests.post(API_URL, json=user_data)
    if user_resp.status_code != 200:
        print("Failed to create normal user token:", user_resp.text)
        exit(1)
    user_token = user_resp.json()["token"]
    print("Normal user token created:", user_token)
    # Now use the normal user token to create the first admin token
    admin_data = {"description": "Admin token", "role": "admin"}
    admin_resp = requests.post(API_URL, json=admin_data, headers={"Authorization": f"Bearer {user_token}"})
    if admin_resp.status_code == 200:
        print("Admin token created:", admin_resp.json()["token"])
    else:
        print("Failed to create admin token:", admin_resp.text)
        exit(1)

if __name__ == "__main__":
    onboard_admin() 
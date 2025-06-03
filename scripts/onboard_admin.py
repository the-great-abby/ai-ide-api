import requests

API_URL = "http://localhost:9103/admin/generate-token"
LIST_URL = "http://localhost:9103/admin/tokens"

def onboard_admin():
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
    # If no admin token, try to create one
    data = {"description": "Admin token", "role": "admin"}
    response = requests.post(API_URL, json=data)
    if response.status_code == 200:
        print("Admin token created:", response.json()["token"])
    else:
        print("Failed to create admin token:", response.text)
        exit(1)

if __name__ == "__main__":
    onboard_admin() 
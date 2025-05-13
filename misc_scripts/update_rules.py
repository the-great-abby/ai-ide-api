import requests
import json
import os

API_URL = os.environ.get("RULE_API_URL", "http://api:8000/rules")
MAPPING_FILE = os.environ.get("RULES_UPDATE_FILE", "rules_update.json")

# Load your mapping from a JSON file
def load_updates(path):
    with open(path) as f:
        return json.load(f)

def main():
    updates = load_updates(MAPPING_FILE)
    for rule_id, data in updates.items():
        resp = requests.patch(
            f"{API_URL}/{rule_id}",
            json={
                "applies_to": data["applies_to"],
                "applies_to_rationale": data["applies_to_rationale"]
            }
        )
        if resp.status_code == 200:
            print(f"Updated rule {rule_id} successfully.")
        else:
            print(f"Failed to update rule {rule_id}: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    main() 
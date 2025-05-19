import json
import os

import requests

API_URL = os.environ.get("RULE_API_URL", "http://api:8000/rules")
OUTPUT_FILE = os.environ.get("RULES_UPDATE_FILE", "rules_update.json")

resp = requests.get(API_URL)
rules = resp.json()

update_dict = {}
for rule in rules:
    update_dict[rule["id"]] = {
        "description": rule.get("description", ""),
        "applies_to": rule.get("applies_to", []),
        "applies_to_rationale": rule.get("applies_to_rationale", ""),
    }

with open(OUTPUT_FILE, "w") as f:
    json.dump(update_dict, f, indent=2)

print(f"Wrote {len(update_dict)} rules to {OUTPUT_FILE}")

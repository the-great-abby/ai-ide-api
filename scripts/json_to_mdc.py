import json
import os

RULES_FILE = "rules.json"
OUTPUT_DIR = "rules_mdc"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load rules from JSON
with open(RULES_FILE, "r") as f:
    rules = json.load(f)

for rule in rules:
    rule_type = rule.get("rule_type", "rule")
    rule_id = rule.get("id", "unknown")
    mdc_content = rule.get("diff", "")
    if not mdc_content:
        continue
    filename = f"{rule_type}_{rule_id}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w") as out:
        out.write(mdc_content)
    print(f"Wrote {filepath}")

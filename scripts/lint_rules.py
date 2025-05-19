import json
import os
import sys

from lint_rule import validate_rule

RULES_FILE = "rules.json"

# Load rules from JSON
with open(RULES_FILE, "r") as f:
    rules = json.load(f)

any_errors = False
for idx, rule in enumerate(rules):
    errors = validate_rule(rule)
    if errors:
        any_errors = True
        print(f"Rule {idx+1} (id={rule.get('id', 'unknown')}): Validation failed:")
        for err in errors:
            print(f"  - {err}")
    else:
        print(f"Rule {idx+1} (id={rule.get('id', 'unknown')}): Valid.")

if any_errors:
    sys.exit(1)
else:
    print("All rules are valid.")

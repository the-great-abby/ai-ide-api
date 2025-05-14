import json
import os

RULES_FILE = "rules.json"
EXPORT_DIR = "exported_rules"
MDC_DIR = os.path.join(EXPORT_DIR, "mdc")

# Ensure output directories exist
os.makedirs(MDC_DIR, exist_ok=True)

# Load rules from JSON
with open(RULES_FILE, "r") as f:
    rules = json.load(f)

# Filter for approved rules
approved_rules = [r for r in rules if r.get("status") == "approved"]

# Write approved rules to JSON (including project field)
approved_json_path = os.path.join(EXPORT_DIR, "approved_rules.json")
with open(approved_json_path, "w") as out:
    json.dump(approved_rules, out, indent=2)
print(f"Exported {len(approved_rules)} approved rules to {approved_json_path}")


# Write each approved rule's MDC to a separate file, organized by project
def get_project(rule):
    return rule.get("project") or "global"


for rule in approved_rules:
    rule_type = rule.get("rule_type", "rule")
    rule_id = rule.get("id", "unknown")
    mdc_content = rule.get("diff", "")
    project = get_project(rule)
    if not mdc_content:
        continue
    project_dir = os.path.join(MDC_DIR, project)
    os.makedirs(project_dir, exist_ok=True)
    filename = f"{rule_type}_{rule_id}.md"
    filepath = os.path.join(project_dir, filename)
    with open(filepath, "w") as out:
        out.write(mdc_content)
    print(f"Wrote {filepath}")

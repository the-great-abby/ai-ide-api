import json
import re
from pathlib import Path

RULES_DIR = Path("/app/ai_ide_rules")

# Simple heuristics for enrichment
KEYWORD_TO_APPLIES = {
    "pytest": ["python", "pytest"],
    "docker": ["docker"],
    "test": ["python", "pytest", "docker"],
    "env": ["docker", "python"],
    "file": ["all"],
    "workflow": ["all"],
    "terminal": ["all"],
    "security": ["all"],
    "mock": ["python", "pytest"],
}

DEFAULT_RATIONALE = "This rule applies to projects using the listed technologies or practices."
DEFAULT_PROJECT = "shared-rules"
DEFAULT_SUBMITTED_BY = "portable-rules-bot"

# Helper to guess rule_type from filename or categories
def guess_rule_type(filename, categories):
    if categories:
        return categories[0]
    if "test" in filename:
        return "testing"
    if "docker" in filename:
        return "environment"
    if "security" in filename:
        return "security"
    if "workflow" in filename:
        return "workflow"
    if "file" in filename:
        return "portability"
    return "general"

# Helper to extract code examples from diff
CODE_BLOCK_RE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.DOTALL)

def extract_examples(diff):
    matches = CODE_BLOCK_RE.findall(diff)
    if matches:
        return "\n---\n" + "\n---\n".join(matches)
    return ""

def enrich_rule(rule, filename):
    changed = False
    # Guess applies_to from filename/description
    applies = set(rule.get("applies_to", []))
    desc = rule.get("description") or ""
    for key, vals in KEYWORD_TO_APPLIES.items():
        if key in filename or key in desc.lower():
            applies.update(vals)
    if applies and applies != set(rule.get("applies_to", [])):
        rule["applies_to"] = sorted(applies)
        changed = True
    # Rationale
    if not rule.get("applies_to_rationale"):
        rule["applies_to_rationale"] = DEFAULT_RATIONALE
        changed = True
    # Rule type
    if not rule.get("rule_type") or rule["rule_type"] == "general":
        rule["rule_type"] = guess_rule_type(filename, rule.get("categories", []))
        changed = True
    # Project
    if not rule.get("project"):
        rule["project"] = DEFAULT_PROJECT
        changed = True
    # Submitted by
    if not rule.get("submitted_by"):
        rule["submitted_by"] = DEFAULT_SUBMITTED_BY
        changed = True
    # Examples
    if not rule.get("examples") and rule.get("diff"):
        ex = extract_examples(rule["diff"])
        if ex:
            rule["examples"] = ex
            changed = True
    # Tags/categories
    if not rule.get("categories"):
        rule["categories"] = [rule["rule_type"]]
        changed = True
    if not rule.get("tags"):
        rule["tags"] = [rule["rule_type"]]
        changed = True
    return changed, rule

def main():
    for json_file in RULES_DIR.glob("*.json"):
        with json_file.open() as f:
            rule = json.load(f)
        changed, enriched = enrich_rule(rule, json_file.name)
        if changed:
            with json_file.open("w") as f:
                json.dump(enriched, f, indent=2)
            print(f"Enriched: {json_file}")
        else:
            print(f"No change: {json_file}")

if __name__ == "__main__":
    main() 
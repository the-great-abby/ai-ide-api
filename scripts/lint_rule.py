import sys
import json
import re

REQUIRED_FIELDS = ["rule_type", "description", "diff", "submitted_by"]


def load_rule():
    if len(sys.argv) > 1:
        # Load from file
        with open(sys.argv[1], "r") as f:
            return json.load(f)
    else:
        # Load from stdin
        return json.load(sys.stdin)

def validate_rule(rule):
    errors = []
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in rule:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(rule[field], str) or not rule[field].strip():
            errors.append(f"Field '{field}' must be a non-empty string")
    # Check MDC formatting in 'diff'
    diff = rule.get("diff", "")
    if not diff.startswith("# Rule:"):
        errors.append("'diff' should start with '# Rule:' (MDC format)")
    if "## Description" not in diff:
        errors.append("'diff' should contain '## Description' section (MDC format)")
    if "## Enforcement" not in diff:
        errors.append("'diff' should contain '## Enforcement' section (MDC format)")
    return errors

if __name__ == "__main__":
    rule = load_rule()
    errors = validate_rule(rule)
    if errors:
        print("Rule validation failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("Rule is valid.") 
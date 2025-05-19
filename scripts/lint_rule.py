import json
import re
import sys
import os

REQUIRED_FIELDS = ["rule_type", "description", "diff", "submitted_by"]


def load_rule(path):
    with open(path, "r") as f:
        return json.load(f)


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
    if not isinstance(diff, str) or not diff.strip():
        errors.append("'diff' must be a non-empty string")
    else:
        if not diff.startswith("# Rule:"):
            errors.append("'diff' should start with '# Rule:' (MDC format)")
        if "## Description" not in diff:
            errors.append("'diff' should contain '## Description' section (MDC format)")
        if "## Enforcement" not in diff:
            errors.append("'diff' should contain '## Enforcement' section (MDC format)")
    return errors


def validate_file(path):
    try:
        rule = load_rule(path)
    except Exception as e:
        return [f"JSON load error: {e}"]
    return validate_rule(rule)


def main():
    if len(sys.argv) < 2:
        print("Usage: python lint_rule.py <file_or_directory>")
        sys.exit(2)
    target = sys.argv[1]
    any_errors = False
    if os.path.isdir(target):
        json_files = [os.path.join(target, f) for f in os.listdir(target) if f.endswith('.json')]
        for path in sorted(json_files):
            errors = validate_file(path)
            if errors:
                any_errors = True
                print(f"{path}: Validation failed:")
                for err in errors:
                    print(f"  - {err}")
            else:
                print(f"{path}: Valid.")
    else:
        errors = validate_file(target)
        if errors:
            any_errors = True
            print(f"{target}: Validation failed:")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"{target}: Valid.")
    if any_errors:
        sys.exit(1)
    else:
        print("All rules are valid.")

if __name__ == "__main__":
    main()

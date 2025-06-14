import json
import re
import sys
import os
import yaml

# Reference: see docs/rules/cursor_mdc_format.md for the full Cursor MDC rule format

REQUIRED_YAML_FIELDS = ["description"]  # globs and alwaysApply are optional
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
REQUIRED_FIELDS = ["rule_type", "description", "diff", "submitted_by"]

def load_json_rule(path):
    with open(path, "r") as f:
        return json.load(f)

def parse_mdc_file(path):
    with open(path, "r") as f:
        text = f.read()
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError("Missing or invalid YAML frontmatter in .mdc file")
    frontmatter = yaml.safe_load(m.group(1))
    body = m.group(2)
    return frontmatter, body

def validate_yaml_frontmatter(frontmatter):
    errors = []
    for field in REQUIRED_YAML_FIELDS:
        if field not in frontmatter:
            errors.append(f"Missing required YAML frontmatter field: {field}")
        elif not isinstance(frontmatter[field], str) or not frontmatter[field].strip():
            errors.append(f"YAML field '{field}' must be a non-empty string")
    # globs and alwaysApply are optional, but if present, check type
    if "globs" in frontmatter and not isinstance(frontmatter["globs"], (list, str)):
        errors.append("YAML field 'globs' should be a string or list")
    if "alwaysApply" in frontmatter and not isinstance(frontmatter["alwaysApply"], bool):
        errors.append("YAML field 'alwaysApply' should be a boolean")
    return errors

def validate_mdc_body(body):
    errors = []
    # Check MDC formatting in 'diff' (body)
    if not body.strip().startswith("# Rule:"):
        errors.append("Body should start with '# Rule:' (MDC format)")
    if "## Description" not in body:
        errors.append("Body should contain '## Description' section (MDC format)")
    if "## Enforcement" not in body:
        errors.append("Body should contain '## Enforcement' section (MDC format)")
    return errors

def validate_mdc_file(path):
    try:
        frontmatter, body = parse_mdc_file(path)
    except Exception as e:
        return [f"YAML frontmatter error: {e}"]
    errors = validate_yaml_frontmatter(frontmatter)
    errors += validate_mdc_body(body)
    return errors

def validate_json_rule(rule):
    errors = []
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

def validate_file(path):
    if path.endswith(".mdc"):
        return validate_mdc_file(path)
    else:
        try:
            rule = load_json_rule(path)
        except Exception as e:
            return [f"JSON load error: {e}"]
        return validate_json_rule(rule)

def main():
    if len(sys.argv) < 2:
        print("Usage: python lint_rule.py <file_or_directory>")
        print("See docs/rules/cursor_mdc_format.md for the Cursor MDC rule format.")
        sys.exit(2)
    target = sys.argv[1]
    any_errors = False
    if os.path.isdir(target):
        files = [os.path.join(target, f) for f in os.listdir(target) if f.endswith('.json') or f.endswith('.mdc')]
        for path in sorted(files):
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
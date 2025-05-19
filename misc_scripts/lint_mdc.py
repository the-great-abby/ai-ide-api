import sys
import os
import re
import yaml

REQUIRED_YAML_FIELDS = ["description", "globs"]

def extract_yaml_frontmatter(path):
    with open(path, "r") as f:
        content = f.read()
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return None, "Missing or malformed YAML frontmatter"
    try:
        frontmatter = yaml.safe_load(match.group(1))
        return frontmatter, None
    except Exception as e:
        return None, f"YAML parse error: {e}"

def validate_yaml_fields(frontmatter):
    errors = []
    for field in REQUIRED_YAML_FIELDS:
        if field not in frontmatter or not str(frontmatter[field]).strip():
            errors.append(f"Missing or empty required YAML field: {field}")
    return errors

def main():
    if len(sys.argv) < 2:
        print("Usage: python lint_mdc.py <file_or_directory>")
        sys.exit(2)
    target = sys.argv[1]
    any_errors = False
    files = []
    if os.path.isdir(target):
        files = [os.path.join(target, f) for f in os.listdir(target) if f.endswith('.mdc')]
    else:
        files = [target]
    for path in files:
        frontmatter, err = extract_yaml_frontmatter(path)
        if err:
            print(f"{path}: {err}")
            any_errors = True
            continue
        errors = validate_yaml_fields(frontmatter)
        if errors:
            print(f"{path}: Validation failed:")
            for e in errors:
                print(f"  - {e}")
            any_errors = True
        else:
            print(f"{path}: Valid YAML frontmatter.")
    if any_errors:
        sys.exit(1)
    else:
        print("All .mdc files are valid.")

if __name__ == "__main__":
    main() 
import os
import json
import re

RULES_DIR = '/app/ai_ide_rules'

DESCRIPTION_PLACEHOLDER = "Placeholder description. Please update."
DIFF_HEADER = "# Rule: <title>\n\n## Description\n<describe the rule>\n\n## Enforcement\n<how to enforce>\n"


def fix_diff(diff, filename):
    changed = False
    # Ensure diff is a string
    if not isinstance(diff, str):
        diff = str(diff)
        changed = True
    # Ensure it starts with # Rule:
    if not diff.strip().startswith('# Rule:'):
        diff = DIFF_HEADER + diff
        changed = True
    # Ensure ## Description section
    if '## Description' not in diff:
        diff = diff + '\n## Description\n<describe the rule>\n'
        changed = True
    # Ensure ## Enforcement section
    if '## Enforcement' not in diff:
        diff = diff + '\n## Enforcement\n<how to enforce>\n'
        changed = True
    return diff, changed


def fix_rule_file(path):
    try:
        with open(path, 'r') as f:
            rule = json.load(f)
    except Exception as e:
        print(f"{path}: Could not load JSON ({e}) - SKIPPED")
        return False
    changed = False
    # Fix description
    if 'description' not in rule or not isinstance(rule['description'], str) or not rule['description'].strip():
        rule['description'] = DESCRIPTION_PLACEHOLDER
        changed = True
    # Fix diff
    if 'diff' in rule:
        fixed_diff, diff_changed = fix_diff(rule['diff'], os.path.basename(path))
        if diff_changed:
            rule['diff'] = fixed_diff
            changed = True
    else:
        rule['diff'] = DIFF_HEADER
        changed = True
    if changed:
        with open(path, 'w') as f:
            json.dump(rule, f, indent=2)
        print(f"{path}: FIXED")
    else:
        print(f"{path}: OK")
    return changed


def main():
    for fname in sorted(os.listdir(RULES_DIR)):
        if fname.endswith('.json'):
            fix_rule_file(os.path.join(RULES_DIR, fname))

if __name__ == "__main__":
    main() 
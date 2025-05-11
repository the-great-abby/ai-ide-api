import os
import re
import sys
import json
from typing import List, Dict
import argparse

# --- Pattern checkers ---

def check_direct_pytest_usage(file_path: str, content: str, project: str = None) -> List[Dict]:
    """
    Suggest a rule if direct pytest usage is found (not via Makefile.ai).
    """
    suggestions = []
    if re.search(r"(^|\s)(pytest|python -m pytest)(\s|$)", content):
        suggestion = {
            "rule_type": "pytest_execution",
            "description": f"Direct pytest usage found in {file_path}. Suggest enforcing Makefile.ai for all pytest runs.",
            "diff": (
                "# Rule: pytest_execution\n\n"
                "## Description\nAll pytest runs must use Makefile.ai.\n\n"
                "## Enforcement\n- Use Makefile.ai targets for all test execution.\n- Do not run pytest directly.\n\n"
                "## Example\n``bash\nmake -f Makefile.ai ai-test PYTEST_ARGS=\"-x\"\n``\n"
            ),
            "submitted_by": "ai-rule-suggester"
        }
        if project:
            suggestion["project"] = project
        suggestions.append(suggestion)
    return suggestions

# Add more pattern checkers here as needed
def pattern_checkers_with_project(project=None):
    return [lambda f, c: check_direct_pytest_usage(f, c, project=project)]

# --- Main suggestion engine ---
def scan_file(file_path: str, project: str = None) -> List[Dict]:
    """
    Scan a single file for rule suggestions using all pattern checkers.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        print(f"[WARN] Could not read {file_path}: {e}")
        return []
    suggestions = []
    for checker in pattern_checkers_with_project(project):
        suggestions.extend(checker(file_path, content))
    return suggestions

def scan_directory(directory: str, project: str = None) -> List[Dict]:
    """
    Recursively scan a directory for rule suggestions.
    """
    suggestions = []
    for root, _, files in os.walk(directory):
        for fname in files:
            if fname.endswith(('.py', '.sh', 'Makefile', '.yml', '.yaml', '.txt', '.md')):
                fpath = os.path.join(root, fname)
                suggestions.extend(scan_file(fpath, project=project))
    return suggestions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Suggest rules based on code patterns.")
    parser.add_argument("target", nargs="?", default=".", help="File or directory to scan")
    parser.add_argument("--project", type=str, default=None, help="Project name or ID to include in suggestions")
    args = parser.parse_args()
    if os.path.isfile(args.target):
        all_suggestions = scan_file(args.target, project=args.project)
    else:
        all_suggestions = scan_directory(args.target, project=args.project)
    print(json.dumps(all_suggestions, indent=2)) 
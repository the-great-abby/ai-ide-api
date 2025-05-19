import argparse
import ast
import json
import os
import re
import sys
from typing import Dict, List

# --- Pattern checkers ---


def check_direct_pytest_usage(
    file_path: str, content: str, project: str = None
) -> List[Dict]:
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
                '## Example\n``bash\nmake -f Makefile.ai ai-test PYTEST_ARGS="-x"\n``\n'
            ),
            "submitted_by": "ai-rule-suggester",
        }
        if project:
            suggestion["project"] = project
        suggestions.append(suggestion)
    return suggestions


def check_direct_sql(file_path: str, content: str, project: str = None) -> List[Dict]:
    suggestions = []
    if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", content, re.IGNORECASE):
        suggestions.append(
            {
                "rule_type": "no_direct_sql",
                "description": f"Direct SQL detected in {file_path}. Use ORM instead.",
                "diff": "# Rule: no_direct_sql\n\n## Description\nAvoid direct SQL queries; use ORM.\n",
                "submitted_by": "ai-rule-suggester",
            }
        )
    return suggestions


def check_print_statements(
    file_path: str, content: str, project: str = None
) -> List[Dict]:
    suggestions = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "print":
                suggestions.append(
                    {
                        "rule_type": "no_print",
                        "description": f"print() statement found in {file_path} at line {node.lineno}.",
                        "diff": "# Rule: no_print\n\n## Description\nAvoid print statements in production code.\n",
                        "submitted_by": "ai-rule-suggester",
                    }
                )
    except Exception:
        pass
    return suggestions


def check_unused_imports(
    file_path: str, content: str, project: str = None
) -> List[Dict]:
    suggestions = []
    import_lines = [
        line for line in content.splitlines() if line.strip().startswith("import ")
    ]
    for line in import_lines:
        # Very basic: flag as unused if the imported name doesn't appear elsewhere
        parts = line.replace("import", "").strip().split()
        for name in parts:
            if name and name not in content.replace(line, ""):
                suggestions.append(
                    {
                        "rule_type": "unused_import",
                        "description": f"Unused import '{name}' in {file_path}.",
                        "diff": "# Rule: unused_import\n\n## Description\nRemove unused imports.\n",
                        "submitted_by": "ai-rule-suggester",
                    }
                )
    return suggestions


def check_hardcoded_secrets(
    file_path: str, content: str, project: str = None
) -> List[Dict]:
    suggestions = []
    # Simple regex for common secret patterns
    if re.search(
        r"(password|secret|api[_-]?key|token)\s*=\s*['\"]", content, re.IGNORECASE
    ):
        suggestions.append(
            {
                "rule_type": "no_hardcoded_secrets",
                "description": f"Possible hardcoded secret detected in {file_path}.",
                "diff": "# Rule: no_hardcoded_secrets\n\n## Description\nDo not hardcode secrets, passwords, or API keys in code. Use environment variables or secret managers.\n",
                "submitted_by": "ai-rule-suggester",
            }
        )
    return suggestions


def check_todo_fixme_comments(
    file_path: str, content: str, project: str = None
) -> List[Dict]:
    suggestions = []
    for i, line in enumerate(content.splitlines(), 1):
        if re.search(r"#\s*(TODO|FIXME)", line, re.IGNORECASE):
            suggestions.append(
                {
                    "rule_type": "todo_fixme_comment",
                    "description": f"{line.strip()} found in {file_path} at line {i}.",
                    "diff": "# Rule: todo_fixme_comment\n\n## Description\nTrack and resolve TODO/FIXME comments promptly.\n",
                    "submitted_by": "ai-rule-suggester",
                }
            )
    return suggestions


def check_eval_usage(file_path: str, content: str, project: str = None) -> List[Dict]:
    suggestions = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "eval":
                suggestions.append(
                    {
                        "rule_type": "no_eval",
                        "description": f"eval() usage found in {file_path} at line {node.lineno}.",
                        "diff": "# Rule: no_eval\n\n## Description\nAvoid use of eval() due to security risks.\n",
                        "submitted_by": "ai-rule-suggester",
                    }
                )
    except Exception:
        pass
    return suggestions


def check_bare_except(file_path: str, content: str, project: str = None) -> List[Dict]:
    suggestions = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                suggestions.append(
                    {
                        "rule_type": "no_bare_except",
                        "description": f"Bare except found in {file_path} at line {node.lineno}.",
                        "diff": "# Rule: no_bare_except\n\n## Description\nDo not use bare except: always specify the exception type.\n",
                        "submitted_by": "ai-rule-suggester",
                    }
                )
    except Exception:
        pass
    return suggestions


def check_wildcard_imports(
    file_path: str, content: str, project: str = None
) -> List[Dict]:
    suggestions = []
    for i, line in enumerate(content.splitlines(), 1):
        if re.match(r"from \\S+ import \\*", line):
            suggestions.append(
                {
                    "rule_type": "no_wildcard_imports",
                    "description": f"Wildcard import found in {file_path} at line {i}.",
                    "diff": "# Rule: no_wildcard_imports\n\n## Description\nAvoid wildcard imports (from module import *).\n",
                    "submitted_by": "ai-rule-suggester",
                }
            )
    return suggestions


def check_long_functions(
    file_path: str, content: str, project: str = None, max_lines: int = 50
) -> List[Dict]:
    suggestions = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start = node.lineno
                end = getattr(node, "end_lineno", None)
                if end is None:
                    # Fallback: estimate end line
                    end = max(
                        [n.lineno for n in ast.walk(node) if hasattr(n, "lineno")],
                        default=start,
                    )
                if end - start + 1 > max_lines:
                    suggestions.append(
                        {
                            "rule_type": "long_function",
                            "description": f"Function '{node.name}' in {file_path} is too long ({end - start + 1} lines, limit {max_lines}).",
                            "diff": f"# Rule: long_function\n\n## Description\nFunctions should not exceed {max_lines} lines. Refactor into smaller functions.\n",
                            "submitted_by": "ai-rule-suggester",
                        }
                    )
    except Exception:
        pass
    return suggestions


def check_missing_docstrings(
    file_path: str, content: str, project: str = None
) -> List[Dict]:
    suggestions = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    suggestions.append(
                        {
                            "rule_type": "missing_docstring",
                            "description": f"Missing docstring for {type(node).__name__} '{getattr(node, 'name', '?')}' in {file_path} at line {node.lineno}.",
                            "diff": "# Rule: missing_docstring\n\n## Description\nAll functions and classes should have docstrings.\n",
                            "submitted_by": "ai-rule-suggester",
                        }
                    )
    except Exception:
        pass
    return suggestions


def check_deprecated_libraries(
    file_path: str, content: str, project: str = None
) -> List[Dict]:
    suggestions = []
    deprecated_libs = ["imp", "optparse", "cgi", "cStringIO", "stringold", "md5", "sha"]
    for i, line in enumerate(content.splitlines(), 1):
        for lib in deprecated_libs:
            if re.match(rf"import {lib}(\s|$)", line) or re.match(
                rf"from {lib} ", line
            ):
                suggestions.append(
                    {
                        "rule_type": "deprecated_library",
                        "description": f"Deprecated library '{lib}' used in {file_path} at line {i}.",
                        "diff": f"# Rule: deprecated_library\n\n## Description\nDo not use deprecated library '{lib}'. Use modern alternatives.\n",
                        "submitted_by": "ai-rule-suggester",
                    }
                )
    return suggestions


def pattern_checkers_with_project(project=None):
    return [
        lambda f, c: check_direct_pytest_usage(f, c, project=project),
        lambda f, c: check_direct_sql(f, c, project=project),
        lambda f, c: check_print_statements(f, c, project=project),
        lambda f, c: check_unused_imports(f, c, project=project),
        lambda f, c: check_hardcoded_secrets(f, c, project=project),
        lambda f, c: check_todo_fixme_comments(f, c, project=project),
        lambda f, c: check_eval_usage(f, c, project=project),
        lambda f, c: check_bare_except(f, c, project=project),
        lambda f, c: check_wildcard_imports(f, c, project=project),
        lambda f, c: check_long_functions(f, c, project=project),
        lambda f, c: check_missing_docstrings(f, c, project=project),
        lambda f, c: check_deprecated_libraries(f, c, project=project),
    ]


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
            if fname.endswith(
                (".py", ".sh", "Makefile", ".yml", ".yaml", ".txt", ".md")
            ):
                fpath = os.path.join(root, fname)
                suggestions.extend(scan_file(fpath, project=project))
    return suggestions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Suggest rules based on code patterns."
    )
    parser.add_argument(
        "target", nargs="?", default=".", help="File or directory to scan"
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Project name or ID to include in suggestions",
    )
    args = parser.parse_args()
    if os.path.isfile(args.target):
        all_suggestions = scan_file(args.target, project=args.project)
    else:
        all_suggestions = scan_directory(args.target, project=args.project)
    print(json.dumps(all_suggestions, indent=2))

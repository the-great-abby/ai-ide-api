import os
import requests
import ast
import logging
import textwrap

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from auth import require_api_token

router = APIRouter(tags=["misc"])

OLLAMA_FUNCTIONS_URL = os.environ.get("OLLAMA_FUNCTIONS_URL", "http://ollama-functions:8000")


def analyze_python_code(code: str):
    """Comprehensive static analysis for Python code."""
    suggestions = []
    # Strip leading/trailing whitespace and dedent code
    code = textwrap.dedent(code).strip()
    try:
        tree = ast.parse(code)
    except Exception as e:
        logging.warning(f"[DEBUG] Failed to parse code: {e}\nCode:\n{code}")
        return suggestions
    # Track function lengths
    for node in ast.walk(tree):
        # Print statements
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            suggestions.append({
                "rule_type": "no_print",
                "description": "Avoid print statements in production code",
                "diff": "-print(...)\n+# Use logging instead of print",
            })
        # Direct pytest usage
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pytest":
                    suggestions.append({
                        "rule_type": "no_direct_pytest",
                        "description": "Avoid direct pytest usage in production code",
                        "diff": "-import pytest\n# Remove direct pytest usage",
                    })
        if isinstance(node, ast.ImportFrom):
            if node.module == "pytest":
                suggestions.append({
                    "rule_type": "no_direct_pytest",
                    "description": "Avoid direct pytest usage in production code",
                    "diff": "-from pytest import ...\n# Remove direct pytest usage",
                })
        # Eval usage
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "eval"
        ):
            suggestions.append({
                "rule_type": "no_eval",
                "description": "Avoid use of eval() for security reasons",
                "diff": "-eval(...)\n+# Avoid eval; use safer alternatives",
            })
        # Bare except
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                suggestions.append({
                    "rule_type": "no_bare_except",
                    "description": "Avoid bare except; catch specific exceptions",
                    "diff": "-except:\n+except ExceptionType:",
                })
        # Wildcard imports
        if isinstance(node, ast.ImportFrom):
            if node.names and any(alias.name == "*" for alias in node.names):
                suggestions.append({
                    "rule_type": "no_wildcard_imports",
                    "description": "Avoid wildcard imports",
                    "diff": "-from module import *\n+from module import specific_function",
                })
        # Deprecated libraries (imp)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "imp":
                    suggestions.append({
                        "rule_type": "deprecated_library",
                        "description": "Avoid using deprecated libraries like 'imp'",
                        "diff": "-import imp\n+import importlib",
                    })
        # Missing docstrings (always check, even for short functions/classes)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not ast.get_docstring(node):
                suggestions.append({
                    "rule_type": "missing_docstring",
                    "description": f"Add a docstring to {node.name}",
                    "diff": f'-def {node.name}(...):\n+def {node.name}(...):\n    """Add docstring here"""',
                })
        # Long functions (over 10 lines for test reliability)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Count lines spanned by the function
            start = getattr(node, 'lineno', None)
            end = getattr(node, 'end_lineno', None)
            if start is not None and end is not None and (end - start + 1) > 10:
                suggestions.append({
                    "rule_type": "long_function",
                    "description": f"Function '{node.name}' is too long ({end - start + 1} lines)",
                    "diff": f'# Consider refactoring {node.name} into smaller functions',
                })
            elif hasattr(node, 'body') and len(node.body) > 10:
                # Fallback for Python <3.8
                suggestions.append({
                    "rule_type": "long_function",
                    "description": f"Function '{node.name}' is too long ({len(node.body)} statements)",
                    "diff": f'# Consider refactoring {node.name} into smaller functions',
                })
    logging.warning(f"[DEBUG] Suggestions generated: {suggestions}")
    return suggestions


@router.post("/review-code-files")
async def review_code_files(
    files: list[UploadFile] = File(...), token: dict = Depends(require_api_token)
):
    """
    Review multiple code files and generate feedback using static analysis.
    Only analyzes .py files; non-Python files return an empty list.
    """
    result = {}
    for file in files:
        if file.filename.endswith(".py"):
            code = (await file.read()).decode("utf-8", errors="ignore")
            logging.warning(f"[DEBUG] Analyzing file: {file.filename}\nCode:\n{code}")
            result[file.filename] = analyze_python_code(code)
        else:
            result[file.filename] = []
    logging.warning(f"[DEBUG] review_code_files result: {result}")
    return result


@router.post("/review-code-files-llm")
async def review_code_files_llm(
    files: list[UploadFile] = File(...), token: dict = Depends(require_api_token)
):
    """
    Review multiple code files using LLM for deeper analysis (Ollama functions).
    Forwards files to the Ollama functions service and returns its response.
    """
    # Prepare files for requests
    file_objs = []
    for file in files:
        content = await file.read()
        file_objs.append(("files", (file.filename, content, file.content_type)))
    try:
        response = requests.post(
            f"{OLLAMA_FUNCTIONS_URL}/review-code-files",
            files=file_objs,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama functions service unavailable: {e}")


@router.post("/review-code-snippet")
async def review_code_snippet(
    request: Request, token: dict = Depends(require_api_token)
):
    """
    Review a single code snippet and generate feedback using static analysis.
    Only analyzes Python code; non-Python code returns an empty list.
    """
    data = await request.json()
    code = data.get("code", "")
    filename = data.get("filename", "snippet.py")
    logging.warning(f"[DEBUG] Analyzing snippet: {filename}\nCode:\n{code}")
    if filename.endswith(".py"):
        suggestions = analyze_python_code(code)
        logging.warning(f"[DEBUG] review_code_snippet suggestions: {suggestions}")
        return suggestions
    return []


@router.get("/changelog", response_class=PlainTextResponse)
async def get_changelog():
    """
    Return the changelog from README.md.

    This endpoint should:
    1. Read the changelog section from README.md
    2. Return it as markdown text
    3. Handle cases where README.md is not found
    """
    try:
        with open("README.md", "r") as f:
            content = f.read()
            # Extract changelog section if it exists
            if "# Changelog" in content:
                changelog_start = content.find("# Changelog")
                next_section = content.find("#", changelog_start + 1)
                if next_section == -1:
                    return content[changelog_start:]
                return content[changelog_start:next_section]
            return content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="README.md not found")


@router.get("/changelog.json")
async def get_changelog_json():
    """
    Return the changelog in JSON format.
    """
    try:
        with open("README.md", "r") as f:
            content = f.read()
            # Extract changelog section if it exists
            if "# Changelog" in content:
                changelog_start = content.find("# Changelog")
                next_section = content.find("#", changelog_start + 1)
                if next_section == -1:
                    changelog_content = content[changelog_start:]
                else:
                    changelog_content = content[changelog_start:next_section]

                # Parse changelog into structured format
                entries = []
                current_version = None
                current_date = None
                current_changes = []

                for line in changelog_content.split("\n"):
                    if line.startswith("## "):
                        if current_version and current_changes:
                            entries.append(
                                {
                                    "version": current_version,
                                    "date": current_date,
                                    "changes": current_changes,
                                }
                            )
                        current_version = line[3:].strip()
                        current_changes = []
                    elif line.startswith("### "):
                        current_date = line[4:].strip()
                    elif line.startswith("- "):
                        current_changes.append(line[2:].strip())

                if current_version and current_changes:
                    entries.append(
                        {
                            "version": current_version,
                            "date": current_date,
                            "changes": current_changes,
                        }
                    )

                return {"changelog": entries}
            return {"changelog": []}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="README.md not found")


@router.get("/pending-rule-changes")
async def get_pending_rule_changes(token: dict = Depends(require_api_token)):
    """
    Get a list of pending rule changes.
    """
    return {"pending_changes": [], "total": 0}

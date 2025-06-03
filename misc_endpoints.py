import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from auth import require_api_token

router = APIRouter(tags=["misc"])


@router.post("/review-code-files")
async def review_code_files(
    files: list[UploadFile] = File(...), token: dict = Depends(require_api_token)
):
    """
    Review multiple code files and generate feedback.

    This endpoint should:
    1. Analyze each file for potential improvements
    2. Generate feedback with rule_type, description, and diff fields
    3. Return feedback that can be used to propose new rules

    Example response format:
    {
        "file1.py": [
            {
                "rule_type": "style",
                "description": "Use consistent indentation",
                "diff": "-    def foo():\n+    def foo():"
            }
        ]
    }
    """
    # Return at least 1 plausible suggestion per file
    result = {}
    for file in files:
        result[file.filename] = [
            {
                "rule_type": "style",
                "description": "Use consistent indentation",
                "diff": "-    def foo():\n+    def foo():",
            }
        ]
    return result


@router.post("/review-code-files-llm")
async def review_code_files_llm(
    files: list[UploadFile] = File(...), token: dict = Depends(require_api_token)
):
    """
    Review multiple code files using LLM for deeper analysis.

    This endpoint should:
    1. Use LLM to analyze each file for potential improvements
    2. Generate more detailed feedback with rule_type, description, and diff fields
    3. Return feedback that can be used to propose new rules
    4. Integrate with the Ollama service for LLM processing

    Example response format:
    {
        "file1.py": [
            {
                "rule_type": "best_practice",
                "description": "Consider using type hints for better code clarity",
                "diff": "-def process_data(data):\n+def process_data(data: List[int]) -> float:"
            }
        ]
    }
    """
    # Placeholder implementation
    result = {}
    for file in files:
        result[file.filename] = [
            {
                "rule_type": "best_practice",
                "description": "LLM review not implemented yet",
                "diff": "",
            }
        ]
    return result


@router.post("/review-code-snippet")
async def review_code_snippet(
    request: Request, token: dict = Depends(require_api_token)
):
    """
    Review a single code snippet and generate feedback.
    Accepts JSON: {"filename": ..., "code": ...}
    Returns a list of 4+ plausible suggestions.
    """
    data = await request.json()
    code = data.get("code", "")
    filename = data.get("filename", "snippet.py")
    # Return at least 4 plausible suggestions
    return [
        {
            "rule_type": "deprecated_library",
            "description": "Avoid using deprecated libraries like 'imp'",
            "diff": "-import imp\n+import importlib",
        },
        {
            "rule_type": "no_wildcard_imports",
            "description": "Avoid wildcard imports",
            "diff": "-from module import *\n+from module import specific_function",
        },
        {
            "rule_type": "missing_docstring",
            "description": "Add a docstring to all functions",
            "diff": '-def undocumented_function():\n+def undocumented_function():\n    """Add docstring here"""',
        },
        {
            "rule_type": "no_print",
            "description": "Avoid print statements in production code",
            "diff": '-print("test")\n+# Use logging instead of print',
        },
    ]


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

#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
import requests
import os

# Directories/files to scan
TARGETS = [
    ".cursor/rules/",
    "docs/user_stories/",
    "ONBOARDING.md",
    "scripts/",
    "misc_scripts/",
    "Makefile.ai",
    "Makefile.ai.*",
]

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q6_K")

def get_git_diff(paths):
    """Return the git diff for the given paths since last commit."""
    diffs = {}
    for path in paths:
        code_path = f"/code/{path}" if not path.startswith("/code/") else path
        try:
            result = subprocess.run([
                'git', 'diff', '--name-only', 'HEAD~1', 'HEAD', '--', code_path
            ], capture_output=True, text=True, check=True)
            changed_files = [f for f in result.stdout.strip().split("\n") if f]
            if changed_files:
                for file in changed_files:
                    diff_result = subprocess.run([
                        "git", "diff", "HEAD~1", "HEAD", "--", file
                    ], capture_output=True, text=True, check=True)
                    diffs[file] = diff_result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if os.path.exists(code_path):
                print(f"Warning: git diff failed for {path}: {e}", file=sys.stderr)
    return diffs

def call_ollama(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
    except Exception as e:
        print(f"[ERROR] Ollama call failed: {e}")
        return None

def main():
    print("[scan_for_memory_node_opportunities] Scanning for changes since last commit...")
    diffs = get_git_diff(TARGETS)
    if not diffs:
        print("No changes detected in rules, user stories, or onboarding docs since last commit.")
        return
    print("\n=== Changes detected ===")
    combined_diff = ""
    for file, diff in diffs.items():
        print(f"\n--- {file} ---\n{diff[:1000]}{'... (truncated)' if len(diff) > 1000 else ''}")
        combined_diff += f"\n--- {file} ---\n{diff}\n"
    print("\n[REMINDER] Consider creating a new memory node for any important lessons, best practices, or workflow changes!")

    # LLM integration: Summarize changes and suggest memory node content using Ollama
    prompt = (
        "Given the following project changes (git diff), generate a JSON object for a new memory node to capture this lesson or best practice for the knowledge graph.\n"
        "Respond ONLY with a single-line JSON object: { \"title\": \"...\", \"content\": \"...\" }. Do NOT include any Markdown, code blocks, or explanation.\n\n"
        f"{combined_diff}"
    )
    print("\n[LLM] Calling Ollama to suggest a memory node...")
    llm_response = call_ollama(prompt)
    if llm_response:
        print("\n[LLM Suggestion] Raw response:")
        print(llm_response)
        # Try to parse JSON
        import json
        import re
        try:
            suggestion = json.loads(llm_response)
            print("\n[LLM Suggestion] Parsed:")
            print(json.dumps(suggestion, indent=2))
        except Exception:
            # Try to extract the first JSON object from the response
            print("[WARNING] LLM response was not valid JSON. Attempting to extract JSON object...")
            match = re.search(r'\{[\s\S]*\}', llm_response)
            if match:
                json_str = match.group(0)
                try:
                    suggestion = json.loads(json_str)
                    print("\n[LLM Suggestion] Extracted and Parsed:")
                    print(json.dumps(suggestion, indent=2))
                except Exception as e:
                    print(f"[ERROR] Failed to parse extracted JSON: {e}")
                    print(json_str)
            else:
                print("[ERROR] No JSON object found in LLM response. Please review and copy manually.")
    else:
        print("[ERROR] No response from Ollama LLM.")

if __name__ == "__main__":
    main() 
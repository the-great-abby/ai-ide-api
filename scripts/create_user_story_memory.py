#!/usr/bin/env python3
import argparse
import sys
import requests
import os
import yaml
import json
import re

# Use Docker service names when running in Docker, otherwise use localhost
API_URL = os.environ.get(
    "MEMORY_API_URL",
    "http://api:8000/memory/nodes" if os.environ.get("RUNNING_IN_DOCKER") else "http://localhost:9103/memory/nodes"
)
OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://api:8000/suggest-llm-rules" if os.environ.get("RUNNING_IN_DOCKER") else "http://localhost:9103/suggest-llm-rules"
)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

def parse_frontmatter_and_content(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    match = FRONTMATTER_RE.match(text)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        content = text[match.end():].strip()
    else:
        frontmatter = {}
        content = text.strip()
    return frontmatter, content

def call_llm_for_summary(content):
    prompt = (
        "Summarize the following user story for onboarding and automation documentation. "
        "Return a concise, clear summary for humans and AI agents.\n\n" + content[:2000]
    )
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
        print(f"[WARNING] LLM summary generation failed: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Create a memory node from a user story markdown file.")
    parser.add_argument('--file', required=True, help='Path to the user story markdown file')
    parser.add_argument('--project', help='Project this memory is associated with (optional)')
    args = parser.parse_args()

    frontmatter, content = parse_frontmatter_and_content(args.file)
    # Required fields
    name = frontmatter.get('name') or os.path.basename(args.file)
    summary = frontmatter.get('summary')
    tags = frontmatter.get('tags', [])
    visibility = frontmatter.get('visibility', 'internal')
    onboarding_paths = frontmatter.get('onboarding_paths', [])
    related_files = frontmatter.get('related_files', [args.file])
    endpoints = frontmatter.get('endpoints', [])
    created_by = frontmatter.get('created_by', '')
    created_at = frontmatter.get('created_at', '')
    updated_at = frontmatter.get('updated_at', '')
    reviewed = frontmatter.get('reviewed', False)
    review_notes = frontmatter.get('review_notes', '')

    # If summary is missing, use LLM to generate one
    if not summary:
        print("[INFO] No summary found in frontmatter. Generating summary with LLM...")
        summary = call_llm_for_summary(content) or content[:200]

    # Build the memory node payload
    node = {
        "namespace": "user_story",
        "content": summary or content,
        "name": name,
        "type": "user_story",
        "summary": summary,
        "description": content,
        "files": related_files,
        "endpoints": endpoints,
        "tags": tags,
        "created_by": created_by,
        "created_at": created_at,
        "updated_at": updated_at,
        "visibility": visibility,
        "onboarding_paths": onboarding_paths,
        "reviewed": reviewed,
        "review_notes": review_notes
    }
    if args.project:
        node["project"] = args.project

    # Submit to the API
    try:
        resp = requests.post(API_URL, json=node)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to create memory: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print("[ERROR] API response:", e.response.text, file=sys.stderr)
        print("[DEBUG] Payload sent:")
        print(json.dumps(node, indent=2))
        sys.exit(1)

    print("[SUCCESS] User story memory node created:")
    print(json.dumps(resp.json(), indent=2))

if __name__ == "__main__":
    main() 
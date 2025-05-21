#!/usr/bin/env python3
import argparse
import sys
import requests
import os

def chunk_text(text, max_tokens=2000):
    # Naive chunking by lines, not tokens
    lines = text.splitlines()
    chunk = []
    chunks = []
    count = 0
    for line in lines:
        chunk.append(line)
        count += 1
        if count >= max_tokens:
            chunks.append("\n".join(chunk))
            chunk = []
            count = 0
    if chunk:
        chunks.append("\n".join(chunk))
    return chunks

# Use Docker service name when running in Docker, otherwise use localhost
OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://api:8000/summarize-git-diff" if os.environ.get("RUNNING_IN_DOCKER") else "http://localhost:9103/summarize-git-diff"
)
MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

VERBOSE_PROMPT = (
    "Provide a detailed, technical summary of the following git diff. "
    "List all changed files, describe the nature of the changes, highlight any new features, "
    "bug fixes, or breaking changes, and include code snippets for the most significant changes. "
    "Be as verbose and explicit as possible."
)
CONCISE_PROMPT = (
    "Summarize the following git diff. List changed files and main changes."
)

def call_ollama(diff_chunk, prompt):
    payload = {
        "model": MODEL,
        "prompt": f"{prompt}\n\n{diff_chunk}",
        "stream": False
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "")

def main():
    parser = argparse.ArgumentParser(description="Summarize a git diff using LLM (Ollama functions).")
    parser.add_argument('--diff-file', help='Path to a git diff file. If omitted, read from stdin.')
    parser.add_argument('--concise', action='store_true', help='Use a concise summary prompt.')
    args = parser.parse_args()

    if args.diff_file:
        with open(args.diff_file, 'r') as f:
            diff = f.read()
    else:
        diff = sys.stdin.read()

    prompt = CONCISE_PROMPT if args.concise else VERBOSE_PROMPT
    chunks = chunk_text(diff, max_tokens=2000)
    summaries = []
    for i, chunk in enumerate(chunks):
        print(f"[INFO] Summarizing chunk {i+1}/{len(chunks)} (length: {len(chunk)} chars)...", file=sys.stderr)
        summary = call_ollama(chunk, prompt)
        summaries.append(summary)
    print("\n==== Combined LLM Summary ====".strip())
    for i, summary in enumerate(summaries):
        print(f"\n--- Chunk {i+1} ---\n{summary.strip()}\n")
    print("==== End of Summary ====")

if __name__ == "__main__":
    main() 
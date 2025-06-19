#!/usr/bin/env python3
import argparse
import sys
import requests
import json
import ast
import os

API_URL = "http://api:8000/memory/nodes"


def get_auth_token():
    """Get API token from /code/.api_admin_token or /code/.apitoken file"""
    token_paths = [
        "/code/.api_admin_token",
        "/code/.apitoken",
        ".api_admin_token",
        ".apitoken",
    ]
    for path in token_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read().strip()
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Create a new memory node via the API."
    )
    parser.add_argument(
        "--name", required=True, help="Short identifier for the memory node"
    )
    parser.add_argument(
        "--observation", required=True, help="Observation or best practice to store"
    )
    parser.add_argument(
        "--project", help="Project this memory is associated with (optional)"
    )
    parser.add_argument(
        "--namespace", required=True, help="Namespace or logical grouping (required)"
    )
    parser.add_argument("--meta", help="Optional JSON string for meta field")
    args = parser.parse_args()

    # Build meta field
    meta = {}
    if args.name:
        meta["name"] = args.name
    if args.project:
        meta["project"] = args.project
    # If --meta is provided, merge it (parsed as JSON)
    if args.meta:
        try:
            user_meta = json.loads(args.meta)
            if isinstance(user_meta, dict):
                meta.update(user_meta)
        except Exception:
            # fallback: try ast.literal_eval for non-strict JSON
            try:
                user_meta = ast.literal_eval(args.meta)
                if isinstance(user_meta, dict):
                    meta.update(user_meta)
            except Exception:
                pass

    # Build the memory node payload
    node = {
        "namespace": args.namespace,
        "content": args.observation,
    }
    if meta:
        node["meta"] = json.dumps(meta)

    # Get API token
    token = get_auth_token()
    if not token:
        print(
            "[ERROR] No API token found. Please ensure /code/.apitoken exists.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Submit to the API
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        resp = requests.post(API_URL, json=node, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        print(
            f"[ERROR] Failed to create memory: {e}\n{getattr(e, 'response', None) and e.response.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    print("[SUCCESS] Memory node created:")
    print(json.dumps(resp.json(), indent=2))


if __name__ == "__main__":
    main()

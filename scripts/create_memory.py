#!/usr/bin/env python3
import argparse
import sys
import requests
import json
import ast
import os

API_URL = "http://api:8000/memory/nodes"


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

    # Get API token from environment
    token = os.environ.get("MEMORY_API_TOKEN")
    if not token:
        print(
            "[ERROR] No API token found. Please ensure MEMORY_API_TOKEN is set.",
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
    except requests.exceptions.HTTPError as e:
        print(
            f"[ERROR] Failed to create memory: {e}\n{e.response.text if e.response else 'No response body'}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(
            f"[ERROR] Failed to create memory: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


    print("[SUCCESS] Memory node created:")
    print(json.dumps(resp.json(), indent=2))


if __name__ == "__main__":
    main()

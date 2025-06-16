#!/usr/bin/env python3
"""
User Story Completeness Checker
Ensures every workflow, Makefile target, or API endpoint has a corresponding user story in docs/user_stories/.
Follows the user story in docs/user_stories/user_story_completeness_checker.md.
"""
import os
import re
import glob
import logging
import argparse
from pathlib import Path

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("user_story_completeness_checker")

USER_STORY_DIR = "docs/user_stories/"
MAKEFILES = ["Makefile", "Makefile.ai"] + glob.glob("Makefile.ai-*")
API_FILES = ["rule_api_server.py", "memory_endpoints.py"]
USER_STORY_TEMPLATE = """# User Story: {name}\n\n## Motivation\n\n## Actors\n\n## Preconditions\n\n## Step-by-Step Actions\n\n## Expected Outcomes\n\n## Best Practices\n"""

def parse_makefile_targets(makefile_path):
    targets = set()
    if not os.path.exists(makefile_path):
        return targets
    with open(makefile_path) as f:
        for line in f:
            m = re.match(r"^([a-zA-Z0-9][a-zA-Z0-9\-_]*)\s*:(?![=])", line)
            if m:
                targets.add(m.group(1))
    return targets

def parse_api_endpoints(api_file):
    endpoints = set()
    if not os.path.exists(api_file):
        return endpoints
    with open(api_file) as f:
        for line in f:
            m = re.search(r"@(app|router)\.(get|post|put|delete)\(\s*['\"](/[^'\"]*)", line)
            if m:
                endpoints.add(m.group(3))
    return endpoints

def list_user_story_files():
    return set(f.name for f in Path(USER_STORY_DIR).glob("*.md"))

def normalize_name(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

def main():
    parser = argparse.ArgumentParser(description="User Story Completeness Checker")
    parser.add_argument("--dry-run", action="store_true", help="Report only, do not create files")
    args = parser.parse_args()

    # Collect all targets and endpoints
    all_targets = set()
    for mf in MAKEFILES:
        all_targets.update(parse_makefile_targets(mf))
    all_endpoints = set()
    for af in API_FILES:
        all_endpoints.update(parse_api_endpoints(af))
    logger.info(f"Found {len(all_targets)} Makefile targets and {len(all_endpoints)} API endpoints.")

    # List user story files
    user_story_files = list_user_story_files()
    logger.info(f"Found {len(user_story_files)} user story files.")

    # Mermaid diagram check
    for filename in user_story_files:
        path = os.path.join(USER_STORY_DIR, filename)
        with open(path) as f:
            content = f.read()
            if '```mermaid' not in content:
                logger.warning(f"[INCOMPLETE] Mermaid diagram missing in user story: {filename}")

    # Check for missing user stories for targets
    missing = []
    for target in sorted(all_targets):
        expected = f"{normalize_name(target)}.md"
        if expected not in user_story_files:
            logger.info(f"[MISSING] User story for Makefile target: {target} (expected: {expected})")
            missing.append((expected, target))
    # Check for missing user stories for endpoints
    for endpoint in sorted(all_endpoints):
        name = endpoint.strip("/").replace("/", "_") or "root"
        expected = f"{normalize_name(name)}.md"
        if expected not in user_story_files:
            logger.info(f"[MISSING] User story for API endpoint: {endpoint} (expected: {expected})")
            missing.append((expected, endpoint))
    # Print template for missing stories
    if missing and not args.dry_run:
        for filename, name in missing:
            path = os.path.join(USER_STORY_DIR, filename)
            if not os.path.exists(path):
                with open(path, "w") as f:
                    f.write(USER_STORY_TEMPLATE.format(name=name))
                logger.info(f"[CREATED] {path}")
    elif missing:
        logger.info("Dry run: No files created. Review log for missing user stories.")
    else:
        logger.info("All targets and endpoints have user stories.")

if __name__ == "__main__":
    main() 
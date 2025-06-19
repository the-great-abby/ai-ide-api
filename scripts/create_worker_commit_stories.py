#!/usr/bin/env python3
"""
Worker Commit Story Generator
Creates detailed, individual stories for specific worker-related commits.
"""

import argparse
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker_commit_stories")

# Worker-related commits we identified from git history analysis
WORKER_COMMITS = [
    {
        "hash": "1912a2b3",
        "description": "things to save - worker container configuration",
        "files": ["Dockerfile.worker", "Makefile.ai-memory", "docker-compose.yml"],
    },
    {
        "hash": "1ae8a7aa",
        "description": "memory workers - comprehensive worker system setup",
        "files": ["Makefile.ai", "Makefile.ai-memory", "Makefile.ai-misc"],
    },
    {
        "hash": "0a7f0f0c",
        "description": "memory worker - similarity pruning implementation",
        "files": [
            "Makefile.ai-memory",
            "docs/user_stories/memory_similarity_pruning_worker.md",
        ],
    },
    {
        "hash": "80417b5f",
        "description": "memory migrations - worker database setup",
        "files": ["Makefile.ai-db", "docs/user_stories/memory_enrichment_worker.md"],
    },
]


def get_commit_info(commit_hash: str) -> Dict[str, Any]:
    """Get detailed information about a specific commit."""
    try:
        # Get commit details
        cmd = [
            "git",
            "show",
            "--no-pager",
            "--pretty=format:%H|%an|%ad|%s",
            "--date=short",
            "--name-only",
            commit_hash,
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd="/code"
        )

        lines = result.stdout.strip().split("\n")
        if not lines:
            return None

        # Parse commit line
        commit_line = lines[0]
        if "|" not in commit_line:
            return None

        parts = commit_line.split("|")
        if len(parts) < 4:
            return None

        full_hash, author, date, message = parts[:4]

        # Get files changed
        files_changed = []
        for line in lines[1:]:
            if line.strip() and not line.startswith("diff"):
                files_changed.append(line.strip())

        return {
            "hash": full_hash,
            "hash_short": commit_hash,
            "author": author,
            "date": date,
            "message": message,
            "files_changed": files_changed,
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get commit info for {commit_hash}: {e}")
        return None


def get_commit_diff(commit_hash: str) -> str:
    """Get the diff for a specific commit."""
    try:
        cmd = ["git", "show", commit_hash, "--no-pager"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd="/code"
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Git show failed for commit {commit_hash}: {e}")
        return ""


def summarize_diff(diff: str, commit_message: str, author: str) -> Dict[str, Any]:
    """Summarize a git diff using the LLM service."""
    if not diff.strip():
        return {"summary": "No changes detected", "categories": [], "tags": []}

    try:
        payload = {
            "diff": diff,
            "commit_msg": commit_message,
            "author": author,
            "concise": False,  # Get more detailed summary for worker commits
        }

        response = requests.post(
            "http://api:8000/summarize-git-diff", json=payload, timeout=120
        )
        response.raise_for_status()

        result = response.json()

        categories = result.get("categories", [])
        tags = result.get("tags", [])
        summary = result.get("combined", result.get("summary", "No summary available"))

        return {"summary": summary, "categories": categories, "tags": tags}

    except Exception as e:
        logger.error(f"Failed to summarize diff: {e}")
        return {"summary": f"Error summarizing diff: {e}", "categories": [], "tags": []}


def create_worker_commit_story(
    commit_info: Dict[str, Any], commit_description: str
) -> Dict[str, Any]:
    """Create a detailed story for a worker-related commit."""

    # Get the diff
    diff = get_commit_diff(commit_info["hash"])

    # Get AI summary
    summary_result = summarize_diff(diff, commit_info["message"], commit_info["author"])

    # Generate detailed story
    story = []
    story.append("=" * 80)
    story.append(f"WORKER COMMIT STORY: {commit_info['hash_short']}")
    story.append("=" * 80)
    story.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    story.append(f"Worker Focus: {commit_description}")
    story.append("")

    # Commit metadata
    story.append("📋 COMMIT METADATA")
    story.append(f"Hash: {commit_info['hash']}")
    story.append(f"Author: {commit_info['author']}")
    story.append(f"Date: {commit_info['date']}")
    story.append(f"Message: {commit_info['message']}")
    story.append("")

    # Files changed
    story.append("📁 FILES CHANGED")
    story.append(f"Total files: {len(commit_info['files_changed'])}")
    for i, file_path in enumerate(commit_info["files_changed"], 1):
        story.append(f"  {i}. {file_path}")
    story.append("")

    # AI Summary
    if summary_result["summary"]:
        story.append("🤖 AI ANALYSIS")
        story.append(summary_result["summary"])
        story.append("")

    # Categories and tags
    if summary_result["categories"] or summary_result["tags"]:
        story.append("🏷️ CLASSIFICATION")
        if summary_result["categories"]:
            story.append(f"Categories: {', '.join(summary_result['categories'])}")
        if summary_result["tags"]:
            story.append(f"Tags: {', '.join(summary_result['tags'])}")
        story.append("")

    # Worker-specific analysis
    story.append("🔧 WORKER-SPECIFIC ANALYSIS")
    story.append(
        f"This commit represents a focused change by {commit_info['author']} related to worker functionality."
    )

    # Analyze worker-related files
    worker_files = [
        f
        for f in commit_info["files_changed"]
        if any(
            keyword in f.lower()
            for keyword in ["worker", "memory", "dockerfile", "makefile"]
        )
    ]
    if worker_files:
        story.append(f"Worker-related files: {len(worker_files)}")
        for file_path in worker_files:
            story.append(f"  • {file_path}")

    # Development context
    story.append("")
    story.append("🔍 DEVELOPMENT CONTEXT")
    story.append(
        f"This commit touches {len(commit_info['files_changed'])} files, suggesting a "
    )

    if len(commit_info["files_changed"]) == 1:
        story.append("targeted modification to a single worker component.")
    elif len(commit_info["files_changed"]) <= 3:
        story.append("moderate scope change affecting a few related worker components.")
    elif len(commit_info["files_changed"]) <= 10:
        story.append("substantial change spanning multiple worker components.")
    else:
        story.append(
            "major refactoring or feature implementation across the worker system."
        )

    # Impact assessment
    story.append("")
    story.append("📊 WORKER IMPACT ASSESSMENT")

    # Analyze file types
    file_extensions = {}
    for file_path in commit_info["files_changed"]:
        ext = os.path.splitext(file_path)[1]
        file_extensions[ext] = file_extensions.get(ext, 0) + 1

    if file_extensions:
        story.append("File types affected:")
        for ext, count in sorted(file_extensions.items()):
            story.append(f"  • {ext or 'no extension'}: {count} files")

    # Worker-specific file analysis
    if any(".py" in ext for ext in file_extensions):
        story.append("  → Python worker code changes detected")
    if any(".md" in ext for ext in file_extensions):
        story.append("  → Worker documentation updates included")
    if any(".yml" in ext or ".yaml" in ext for ext in file_extensions):
        story.append("  → Worker configuration changes made")
    if any("dockerfile" in f.lower() for f in commit_info["files_changed"]):
        story.append("  → Worker container configuration modified")
    if any("makefile" in f.lower() for f in commit_info["files_changed"]):
        story.append("  → Worker build/management scripts updated")

    story.append("")
    story.append("=" * 80)

    return {
        "content": "\n".join(story),
        "meta": {
            "type": "worker_commit_story",
            "commit_hash": commit_info["hash"],
            "commit_hash_short": commit_info["hash_short"],
            "author": commit_info["author"],
            "date": commit_info["date"],
            "message": commit_info["message"],
            "files_changed": commit_info["files_changed"],
            "file_count": len(commit_info["files_changed"]),
            "categories": summary_result["categories"],
            "tags": summary_result["tags"],
            "summary": summary_result["summary"],
            "story_length": len("\n".join(story)),
            "generated_at": datetime.now().isoformat(),
            "worker_focus": commit_description,
        },
        "namespace": "worker_commits",
        "tags": [
            "worker-commit",
            "detailed-story",
            "git-history",
            f"commit-{commit_info['hash_short']}",
            f"author-{commit_info['author'].lower().replace(' ', '-')}",
            f"date-{commit_info['date']}",
            "worker-system",
            "memory-workers",
        ]
        + summary_result["categories"]
        + summary_result["tags"],
    }


def store_commit_story(story_data: Dict[str, Any], api_token: str) -> str:
    """Store the commit story in the memory system."""
    try:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "content": story_data["content"],
            "meta": json.dumps(story_data["meta"]),
            "namespace": story_data["namespace"],
            "tags": story_data["tags"],
        }

        response = requests.post(
            "http://api:8000/memory/nodes", json=payload, headers=headers, timeout=30
        )
        response.raise_for_status()

        result = response.json()
        return result.get("id", "unknown")

    except Exception as e:
        logger.error(f"Failed to store commit story: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Create individual detailed stories for worker-related commits"
    )
    parser.add_argument("--api-token", help="API token for memory storage")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without storing",
    )

    args = parser.parse_args()

    # Get API token
    api_token = args.api_token
    if not api_token:
        try:
            with open("/code/.apitoken", "r") as f:
                api_token = f.read().strip()
        except FileNotFoundError:
            logger.error("No API token provided and .apitoken file not found")
            sys.exit(1)

    logger.info("Creating individual stories for worker-related commits...")

    # Process each worker commit
    created_stories = []
    for worker_commit in WORKER_COMMITS:
        commit_hash = worker_commit["hash"]
        description = worker_commit["description"]

        logger.info(f"Processing worker commit: {commit_hash} - {description}")

        try:
            # Get commit info
            commit_info = get_commit_info(commit_hash)
            if not commit_info:
                logger.error(f"Failed to get info for commit {commit_hash}")
                continue

            # Create individual story
            story_data = create_worker_commit_story(commit_info, description)

            if args.dry_run:
                logger.info(
                    f"DRY RUN: Would create worker story for commit {commit_hash}"
                )
                logger.info(
                    f"Story length: {story_data['meta']['story_length']} characters"
                )
                logger.info(f"Files changed: {story_data['meta']['file_count']}")
                continue

            # Store in memory system
            memory_id = store_commit_story(story_data, api_token)

            if memory_id:
                logger.info(
                    f"✅ Created worker story for commit {commit_hash} (ID: {memory_id})"
                )
                created_stories.append(
                    {
                        "commit_hash": commit_hash,
                        "memory_id": memory_id,
                        "author": commit_info["author"],
                        "date": commit_info["date"],
                        "files": len(commit_info["files_changed"]),
                        "description": description,
                    }
                )
            else:
                logger.error(f"❌ Failed to store worker story for commit {commit_hash}")

        except Exception as e:
            logger.error(f"Error processing worker commit {commit_hash}: {e}")
            continue

    # Summary
    logger.info("=" * 60)
    logger.info("WORKER COMMIT STORIES SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total worker commits processed: {len(WORKER_COMMITS)}")
    logger.info(f"Stories created: {len(created_stories)}")

    if created_stories:
        logger.info("")
        logger.info("Created worker stories:")
        for story in created_stories:
            logger.info(
                f"  • {story['commit_hash']} by {story['author']} ({story['files']} files)"
            )
            logger.info(f"    → {story['description']}")
            logger.info(f"    → Memory ID: {story['memory_id']}")
            logger.info("")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()

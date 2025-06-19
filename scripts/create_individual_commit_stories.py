#!/usr/bin/env python3
"""
Individual Commit Story Generator
Creates detailed, individual stories for each commit in a git history range.
Each commit gets its own memory node with a comprehensive narrative.
"""

import argparse
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
import subprocess

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.git_history_analyzer import get_commit_list, analyze_commit, GitCommit
from utils.message_broker import RealRabbitMQClient
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("individual_commit_stories")


def get_commit_list_fixed(
    since: str = None, until: str = None, max_commits: int = 50, author: str = None
) -> List[GitCommit]:
    """Get a list of commits with metadata - fixed for misc-scripts container."""
    commits = []

    # Build git log command
    cmd = ["git", "log", "--pretty=format:%H|%an|%ad|%s", "--date=short", "--name-only"]

    if since:
        cmd.extend(["--since", since])
    if until:
        cmd.extend(["--until", until])
    if author:
        cmd.extend(["--author", author])

    cmd.extend(["-n", str(max_commits)])

    try:
        # Use /code directory where the .git folder is mounted
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd="/code"
        )
        lines = result.stdout.strip().split("\n")

        current_commit = None
        for line in lines:
            if "|" in line:  # This is a commit line
                parts = line.split("|")
                if len(parts) >= 4:
                    commit_hash, author_name, date, subject = parts[:4]
                    current_commit = GitCommit(
                        commit_hash=commit_hash,
                        author=author_name,
                        date=date,
                        message=subject,
                        files_changed=[],
                    )
                    commits.append(current_commit)
            elif line.strip() and current_commit:  # This is a file line
                current_commit.files_changed.append(line.strip())

    except subprocess.CalledProcessError as e:
        logger.error(f"Git log failed: {e}")
        return []

    return commits


def get_commit_diff_fixed(commit_hash: str) -> str:
    """Get the diff for a specific commit - fixed for misc-scripts container."""
    try:
        cmd = ["git", "show", commit_hash, "--no-pager"]

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd="/code"
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Git show failed for commit {commit_hash}: {e}")
        return ""


def analyze_commit_fixed(
    commit: GitCommit, include_diff: bool = True, summarize: bool = True
) -> GitCommit:
    """Analyze a single commit by getting its diff and summary - fixed version."""
    logger.info(f"Analyzing commit {commit.commit_hash[:8]} by {commit.author}")

    # Get diff
    if include_diff:
        commit.diff = get_commit_diff_fixed(commit.commit_hash)

    # Summarize if requested
    if summarize and commit.diff:
        summary_result = summarize_diff(
            commit.diff, commit.message, commit.author, concise=True
        )
        commit.summary = summary_result["summary"]
        commit.categories = summary_result["categories"]
        commit.tags = summary_result["tags"]

    return commit


def summarize_diff(
    diff: str, commit_message: str, author: str, concise: bool = True
) -> Dict[str, Any]:
    """Summarize a git diff using the LLM service."""
    if not diff.strip():
        return {"summary": "No changes detected", "categories": [], "tags": []}

    try:
        payload = {
            "diff": diff,
            "commit_msg": commit_message,
            "author": author,
            "concise": concise,
        }

        response = requests.post(
            "http://api:8000/summarize-git-diff", json=payload, timeout=120
        )
        response.raise_for_status()

        result = response.json()

        # Extract categories and tags if available
        categories = result.get("categories", [])
        tags = result.get("tags", [])
        summary = result.get("combined", result.get("summary", "No summary available"))

        return {"summary": summary, "categories": categories, "tags": tags}

    except Exception as e:
        logger.error(f"Failed to summarize diff: {e}")
        return {"summary": f"Error summarizing diff: {e}", "categories": [], "tags": []}


def create_individual_commit_story(
    commit: GitCommit, memory_namespace: str = "individual_commits"
) -> Dict[str, Any]:
    """Create a detailed story for a single commit."""

    # Analyze the commit with full details
    analyzed_commit = analyze_commit_fixed(commit, include_diff=True, summarize=True)

    # Generate a detailed story for this single commit
    story = []
    story.append("=" * 80)
    story.append(f"COMMIT STORY: {analyzed_commit.commit_hash[:8]}")
    story.append("=" * 80)
    story.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    story.append("")

    # Commit metadata
    story.append("📋 COMMIT METADATA")
    story.append(f"Hash: {analyzed_commit.commit_hash}")
    story.append(f"Author: {analyzed_commit.author}")
    story.append(f"Date: {analyzed_commit.date}")
    story.append(f"Message: {analyzed_commit.message}")
    story.append("")

    # Files changed
    story.append("📁 FILES CHANGED")
    story.append(f"Total files: {len(analyzed_commit.files_changed)}")
    for i, file_path in enumerate(analyzed_commit.files_changed, 1):
        story.append(f"  {i}. {file_path}")
    story.append("")

    # AI Summary
    if analyzed_commit.summary:
        story.append("🤖 AI ANALYSIS")
        story.append(analyzed_commit.summary)
        story.append("")

    # Categories and tags
    if analyzed_commit.categories or analyzed_commit.tags:
        story.append("🏷️ CLASSIFICATION")
        if analyzed_commit.categories:
            story.append(f"Categories: {', '.join(analyzed_commit.categories)}")
        if analyzed_commit.tags:
            story.append(f"Tags: {', '.join(analyzed_commit.tags)}")
        story.append("")

    # Development context
    story.append("🔍 DEVELOPMENT CONTEXT")
    story.append(
        f"This commit represents a focused change by {analyzed_commit.author}."
    )
    story.append(
        f"It touches {len(analyzed_commit.files_changed)} files, suggesting a "
    )

    if len(analyzed_commit.files_changed) == 1:
        story.append("targeted modification to a single component.")
    elif len(analyzed_commit.files_changed) <= 3:
        story.append("moderate scope change affecting a few related components.")
    elif len(analyzed_commit.files_changed) <= 10:
        story.append("substantial change spanning multiple components.")
    else:
        story.append("major refactoring or feature implementation across the codebase.")

    # Impact assessment
    story.append("")
    story.append("📊 IMPACT ASSESSMENT")

    # Analyze file types
    file_extensions = {}
    for file_path in analyzed_commit.files_changed:
        ext = os.path.splitext(file_path)[1]
        file_extensions[ext] = file_extensions.get(ext, 0) + 1

    if file_extensions:
        story.append("File types affected:")
        for ext, count in sorted(file_extensions.items()):
            story.append(f"  • {ext or 'no extension'}: {count} files")

    # Check for specific file types
    if any(".py" in ext for ext in file_extensions):
        story.append("  → Python code changes detected")
    if any(".md" in ext for ext in file_extensions):
        story.append("  → Documentation updates included")
    if any(".yml" in ext or ".yaml" in ext for ext in file_extensions):
        story.append("  → Configuration changes made")
    if any(".json" in ext for ext in file_extensions):
        story.append("  → Data structure modifications")

    story.append("")
    story.append("=" * 80)

    return {
        "content": "\n".join(story),
        "meta": {
            "type": "individual_commit_story",
            "commit_hash": analyzed_commit.commit_hash,
            "commit_hash_short": analyzed_commit.commit_hash[:8],
            "author": analyzed_commit.author,
            "date": analyzed_commit.date,
            "message": analyzed_commit.message,
            "files_changed": analyzed_commit.files_changed,
            "file_count": len(analyzed_commit.files_changed),
            "categories": analyzed_commit.categories,
            "tags": analyzed_commit.tags,
            "summary": analyzed_commit.summary,
            "story_length": len("\n".join(story)),
            "generated_at": datetime.now().isoformat(),
        },
        "namespace": memory_namespace,
        "tags": [
            "individual-commit",
            "detailed-story",
            "git-history",
            f"commit-{analyzed_commit.commit_hash[:8]}",
            f"author-{analyzed_commit.author.lower().replace(' ', '-')}",
            f"date-{analyzed_commit.date}",
        ]
        + analyzed_commit.categories
        + analyzed_commit.tags,
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
        description="Create individual detailed stories for each commit"
    )
    parser.add_argument(
        "--since", help="Start date (e.g., '2024-01-01' or '2 days ago')"
    )
    parser.add_argument("--until", help="End date (e.g., '2024-01-31')")
    parser.add_argument(
        "--max-commits",
        type=int,
        default=10,
        help="Maximum number of commits to analyze",
    )
    parser.add_argument("--author", help="Filter by author")
    parser.add_argument(
        "--memory-namespace",
        default="individual_commits",
        help="Memory namespace for stories",
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

    # Get commit list
    logger.info("Fetching commit list...")
    commits = get_commit_list_fixed(
        since=args.since,
        until=args.until,
        max_commits=args.max_commits,
        author=args.author,
    )

    if not commits:
        logger.warning("No commits found matching criteria")
        return

    logger.info(f"Found {len(commits)} commits to analyze")

    # Process each commit
    created_stories = []
    for i, commit in enumerate(commits, 1):
        logger.info(
            f"Processing commit {i}/{len(commits)}: {commit.commit_hash[:8]} by {commit.author}"
        )

        try:
            # Create individual story
            story_data = create_individual_commit_story(commit, args.memory_namespace)

            if args.dry_run:
                logger.info(
                    f"DRY RUN: Would create story for commit {commit.commit_hash[:8]}"
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
                    f"✅ Created story for commit {commit.commit_hash[:8]} (ID: {memory_id})"
                )
                created_stories.append(
                    {
                        "commit_hash": commit.commit_hash[:8],
                        "memory_id": memory_id,
                        "author": commit.author,
                        "date": commit.date,
                        "files": len(commit.files_changed),
                    }
                )
            else:
                logger.error(
                    f"❌ Failed to store story for commit {commit.commit_hash[:8]}"
                )

        except Exception as e:
            logger.error(f"Error processing commit {commit.commit_hash[:8]}: {e}")
            continue

    # Summary
    logger.info("=" * 60)
    logger.info("INDIVIDUAL COMMIT STORIES SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total commits processed: {len(commits)}")
    logger.info(f"Stories created: {len(created_stories)}")

    if created_stories:
        logger.info("")
        logger.info("Created stories:")
        for story in created_stories:
            logger.info(
                f"  • {story['commit_hash']} by {story['author']} ({story['files']} files) → {story['memory_id']}"
            )

    logger.info("=" * 60)


if __name__ == "__main__":
    main()

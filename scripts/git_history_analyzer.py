#!/usr/bin/env python3
"""
Git History Analyzer
Traverses git history and gathers summaries of changes across multiple commits.
Builds on existing git diff functionality to provide comprehensive change analysis.
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import requests
import os
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("git_history_analyzer")

# Configuration
GIT_DIFF_SUMMARY_URL = os.environ.get(
    "GIT_DIFF_SUMMARY_URL",
    "http://ollama-functions:8000/summarize-git-diff"
    if os.environ.get("RUNNING_IN_DOCKER")
    else "http://localhost:9103/summarize-git-diff",
)

# Keep the original OLLAMA_URL for backward compatibility (not used in this script)
OLLAMA_URL = os.environ.get(
    "OLLAMA_URL", "http://host.docker.internal:11434/api/generate"
)

# Throttling and retry configuration
DEFAULT_BATCH_SIZE = 2  # Reduced from 3 to be more conservative
DEFAULT_BATCH_DELAY = 8  # Increased from 5 seconds
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 15  # Increased base delay from 10 seconds
DEFAULT_MAX_RETRIES = 5
DEFAULT_REQUEST_TIMEOUT = 180  # Increased timeout from 120 seconds
DEFAULT_JITTER_MIN = 2.0  # Minimum jitter in seconds
DEFAULT_JITTER_MAX = 8.0  # Maximum jitter in seconds


class GitCommit:
    """Represents a single git commit with metadata."""

    def __init__(
        self,
        commit_hash: str,
        author: str,
        date: str,
        message: str,
        files_changed: List[str],
    ):
        self.commit_hash = commit_hash
        self.author = author
        self.date = date
        self.message = message
        self.files_changed = files_changed
        self.diff = ""
        self.summary = ""
        self.categories = []
        self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commit_hash": self.commit_hash,
            "author": self.author,
            "date": self.date,
            "message": self.message,
            "files_changed": self.files_changed,
            "diff": self.diff,
            "summary": self.summary,
            "categories": self.categories,
            "tags": self.tags,
        }


def get_commit_list(
    since: Optional[str] = None,
    until: Optional[str] = None,
    max_commits: int = 50,
    author: Optional[str] = None,
) -> List[GitCommit]:
    """Get a list of commits from git log."""
    commits = []

    cmd = ["git", "log", "--pretty=format:%H|%an|%ad|%s", "--date=short"]

    if since:
        cmd.extend(["--since", since])
    if until:
        cmd.extend(["--until", until])
    if author:
        cmd.extend(["--author", author])

    cmd.extend(["-n", str(max_commits)])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd="."
        )
        lines = result.stdout.strip().split("\n")

        for line in lines:
            if "|" in line:  # This is a commit line
                parts = line.split("|")
                if len(parts) >= 4:
                    commit_hash, author_name, date, subject = parts[:4]
                    
                    # Get files changed for this commit
                    files_changed = get_commit_files(commit_hash)
                    
                    current_commit = GitCommit(
                        commit_hash=commit_hash,
                        author=author_name,
                        date=date,
                        message=subject,
                        files_changed=files_changed,
                    )
                    commits.append(current_commit)

    except subprocess.CalledProcessError as e:
        logger.error(f"Git log failed: {e}")
        return []

    return commits


def get_commit_files(commit_hash: str) -> List[str]:
    """Get the list of files changed in a specific commit."""
    try:
        cmd = ["git", "show", "--name-only", "--pretty=format:", commit_hash]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd="."
        )
        
        # Split output and filter out empty lines
        files = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        return files
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git show failed for commit {commit_hash}: {e}")
        return []


def get_commit_diff(commit_hash: str) -> str:
    """Get the diff for a specific commit."""
    try:
        cmd = ["git", "show", commit_hash]

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd="."
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Git show failed for commit {commit_hash}: {e}")
        return ""


def get_parent_commit(commit_hash: str) -> Optional[str]:
    """Get the parent commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", f"{commit_hash}^"],
            capture_output=True,
            text=True,
            check=True,
            cwd=".",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def summarize_diff(
    diff: str, commit_message: str, author: str, concise: bool = True, health_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Summarize a git diff using the LLM service with improved retry logic and adaptive timeouts."""
    if not diff.strip():
        return {"summary": "No changes detected", "categories": [], "tags": []}

    payload = {
        "diff": diff,
        "commit_msg": commit_message,
        "author": author,
        "concise": concise,
    }

    # Get adaptive timeout based on health data
    if health_data:
        timeout = get_adaptive_timeout(health_data)
        logger.info(f"Using adaptive timeout: {timeout}s (load level: {health_data.get('load_level', 'unknown')})")
    else:
        timeout = DEFAULT_REQUEST_TIMEOUT
        logger.info(f"Using default timeout: {timeout}s")

    # Improved retry logic with exponential backoff and jitter
    for attempt in range(DEFAULT_RETRY_ATTEMPTS):
        try:
            logger.info(f"Attempting LLM summarization (attempt {attempt + 1}/{DEFAULT_RETRY_ATTEMPTS})")
            response = requests.post(GIT_DIFF_SUMMARY_URL, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ LLM summarization successful (attempt {attempt + 1})")
                return result
            else:
                logger.warning(f"HTTP {response.status_code} from LLM service")
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1} (timeout: {timeout}s)")
            # Aggressive timeout handling - longer delays for timeouts
            base_delay = DEFAULT_RETRY_DELAY * (3 ** attempt)  # Exponential backoff for timeouts
            jitter = random.uniform(DEFAULT_JITTER_MIN, DEFAULT_JITTER_MAX)
            delay = base_delay + jitter
            logger.info(f"Waiting {delay:.1f}s before retry...")
            time.sleep(delay)
            continue
            
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error on attempt {attempt + 1}")
            # Moderate delays for connection errors
            base_delay = DEFAULT_RETRY_DELAY * (2 ** attempt)
            jitter = random.uniform(DEFAULT_JITTER_MIN, DEFAULT_JITTER_MAX)
            delay = base_delay + jitter
            logger.info(f"Waiting {delay:.1f}s before retry...")
            time.sleep(delay)
            continue
            
        except Exception as e:
            logger.error(f"Unexpected error during LLM summarization: {e}")
            return {"summary": f"Error summarizing diff: {e}", "categories": [], "tags": []}

    # Fallback return in case all attempts fail but loop exits without returning
    logger.error("All LLM summarization attempts failed")
    return {"summary": "Error: All summarization attempts failed", "categories": [], "tags": []}


def analyze_commit(
    commit: GitCommit, include_diff: bool = True, summarize: bool = True, health_data: Optional[Dict[str, Any]] = None
) -> GitCommit:
    """Analyze a single commit with optional health data for adaptive timeouts."""
    if include_diff and commit.diff is None:
        commit.diff = get_commit_diff(commit.commit_hash)

    if summarize and commit.diff:
        try:
            summary_result = summarize_diff(
                commit.diff, commit.message, commit.author, concise=True, health_data=health_data
            )
            commit.summary = summary_result.get("summary", "")
            commit.categories = summary_result.get("categories", [])
            commit.tags = summary_result.get("tags", [])
        except Exception as e:
            logger.error(f"Failed to summarize commit {commit.commit_hash}: {e}")
            commit.summary = f"Error: {e}"
            commit.categories = []
            commit.tags = []

    return commit


def analyze_commit_range(
    commits: List[GitCommit],
    include_diff: bool = True,
    summarize: bool = True,
    batch_size: int = DEFAULT_BATCH_SIZE,
    health_data: Optional[Dict[str, Any]] = None,
) -> List[GitCommit]:
    """Analyze a range of commits with improved throttling and error handling."""
    analyzed_commits = []
    total_commits = len(commits)
    
    logger.info(f"Starting analysis of {total_commits} commits with batch_size={batch_size}")

    for i, commit in enumerate(commits):
        logger.info(f"Processing commit {i+1}/{total_commits}: {commit.commit_hash[:8]}")

        try:
            analyzed_commit = analyze_commit(commit, include_diff, summarize, health_data)
            analyzed_commits.append(analyzed_commit)
            
            # Progress tracking
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{total_commits} commits processed")
            
            # Adaptive batch processing with jitter
            if (i + 1) % batch_size == 0 and i < total_commits - 1:
                # Get current health status for adaptive delays
                current_health = check_ollama_health() if health_data else None
                load_level = current_health.get("load_level", "normal") if current_health else "normal"
                
                if load_level == "high":
                    base_delay = DEFAULT_BATCH_DELAY * 2  # Double delay when overloaded
                elif load_level == "degraded":
                    base_delay = DEFAULT_BATCH_DELAY * 1.5  # 1.5x delay when degraded
                else:
                    base_delay = DEFAULT_BATCH_DELAY
                
                jitter = random.uniform(DEFAULT_JITTER_MIN, DEFAULT_JITTER_MAX)
                delay = base_delay + jitter
                
                logger.info(f"Batch complete. Waiting {delay:.1f}s before next batch (load: {load_level})...")
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"Failed to analyze commit {commit.commit_hash[:8]}: {e}")
            # Continue with next commit instead of failing completely
            analyzed_commits.append(commit)

    logger.info(f"✅ Analysis complete: {len(analyzed_commits)}/{total_commits} commits processed")
    return analyzed_commits


def generate_report(commits: List[GitCommit], output_format: str = "json") -> str:
    """Generate a report from analyzed commits."""
    if output_format == "json":
        return json.dumps([commit.to_dict() for commit in commits], indent=2)

    elif output_format == "text":
        report = []
        report.append("=" * 80)
        report.append("GIT HISTORY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total commits analyzed: {len(commits)}")
        report.append("")

        for i, commit in enumerate(commits, 1):
            report.append(f"Commit {i}: {commit.commit_hash[:8]}")
            report.append(f"Author: {commit.author}")
            report.append(f"Date: {commit.date}")
            report.append(f"Message: {commit.message}")
            report.append(f"Files changed: {len(commit.files_changed)}")

            if commit.summary:
                report.append(f"Summary: {commit.summary}")

            if commit.categories:
                report.append(f"Categories: {', '.join(commit.categories)}")

            if commit.tags:
                report.append(f"Tags: {', '.join(commit.tags)}")

            report.append("-" * 40)

        return "\n".join(report)

    elif output_format == "story":
        """Generate a concise narrative story of the development progression."""
        if not commits:
            return "No commits found to create a story from."

        # Sort commits by date (oldest first for story progression)
        sorted_commits = sorted(commits, key=lambda x: x.date)

        story = []
        story.append("DEVELOPMENT STORY")
        story.append(f"Period: {sorted_commits[0].date} to {sorted_commits[-1].date}")
        story.append(f"Commits: {len(sorted_commits)}")
        story.append("")

        # Calculate overall statistics
        total_files = sum(len(c.files_changed) for c in sorted_commits)
        authors = set(c.author for c in sorted_commits)
        all_categories = set()
        all_tags = set()

        for commit in sorted_commits:
            all_categories.update(commit.categories)
            all_tags.update(commit.tags)

        # Key insights
        story.append("KEY INSIGHTS:")
        story.append(f"• Contributors: {', '.join(authors)}")
        story.append(f"• Files changed: {total_files}")
        if all_categories:
            story.append(f"• Focus areas: {', '.join(list(all_categories)[:3])}")
        story.append("")

        # Group commits by themes/categories
        category_groups = {}
        for commit in sorted_commits:
            for category in commit.categories:
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(commit)

        # Tell the story by themes (concise)
        if category_groups:
            story.append("MAJOR THEMES:")
            for category, category_commits in category_groups.items():
                story.append(f"• {category}: {len(category_commits)} commits")
                # Show only the most recent commit in each category
                latest_commit = max(category_commits, key=lambda x: x.date)
                story.append(f"  Latest: {latest_commit.message}")
            story.append("")

        # Recent activity summary
        story.append("RECENT ACTIVITY:")
        recent_commits = sorted_commits[-5:]  # Last 5 commits
        for commit in recent_commits:
            story.append(f"• {commit.date}: {commit.message}")
            if commit.summary and len(commit.summary) < 100:
                story.append(f"  {commit.summary}")
        story.append("")

        # Development patterns
        story.append("PATTERNS:")
        author_counts = {}
        for commit in sorted_commits:
            author_counts[commit.author] = author_counts.get(commit.author, 0) + 1

        most_active_author = max(author_counts.items(), key=lambda x: x[1])
        story.append(
            f"• Most active: {most_active_author[0]} ({most_active_author[1]} commits)"
        )
        story.append(f"• Avg files per commit: {total_files / len(sorted_commits):.1f}")

        return "\n".join(story)

    elif output_format == "summary":
        # Generate a high-level summary
        total_files = sum(len(c.files_changed) for c in commits)
        authors = set(c.author for c in commits)
        categories = set()
        tags = set()

        for commit in commits:
            categories.update(commit.categories)
            tags.update(commit.tags)

        summary = {
            "total_commits": len(commits),
            "total_files_changed": total_files,
            "unique_authors": len(authors),
            "authors": list(authors),
            "categories": list(categories),
            "tags": list(tags),
            "date_range": {
                "start": commits[-1].date if commits else None,
                "end": commits[0].date if commits else None,
            },
        }

        return json.dumps(summary, indent=2)

    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def check_llm_service_health() -> bool:
    """Check if the LLM service is healthy and responding."""
    try:
        logger.info(f"Checking LLM service health at {GIT_DIFF_SUMMARY_URL}")
        response = requests.get(GIT_DIFF_SUMMARY_URL.replace("/summarize-git-diff", "/health"), timeout=10)
        if response.status_code == 200:
            logger.info("✅ LLM service is healthy and responding")
            return True
        else:
            logger.warning(f"LLM service returned status {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"LLM service health check failed: {e}")
        return False


def check_ollama_health() -> Dict[str, Any]:
    """Check Ollama health and get load information."""
    try:
        logger.info("Checking Ollama health before starting analysis...")
        response = requests.get(f"{GIT_DIFF_SUMMARY_URL.replace('/summarize-git-diff', '/health')}", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"Ollama health: {health_data.get('status', 'unknown')}")
            logger.info(f"Response time: {health_data.get('response_time', 'unknown')}s")
            logger.info(f"Load level: {health_data.get('load_level', 'unknown')}")
            return health_data
        else:
            logger.warning(f"Ollama health check returned status {response.status_code}")
            return {"status": "error", "load_level": "unknown"}
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        return {"status": "error", "load_level": "unknown"}


def get_adaptive_timeout(health_data: Dict[str, Any]) -> int:
    """Get adaptive timeout based on Ollama health."""
    load_level = health_data.get("load_level", "normal")
    avg_response_time = health_data.get("avg_response_time", 0)
    
    if load_level == "high" or avg_response_time > 30:
        return 300  # 5 minutes for high load
    elif load_level == "degraded" or avg_response_time > 15:
        return 240  # 4 minutes for degraded
    else:
        return 180  # 3 minutes for normal load


def get_adaptive_batch_size(total_commits: int, health_data: Dict[str, Any]) -> int:
    """Get an adaptive batch size based on total commits and Ollama health."""
    load_level = health_data.get("load_level", "normal")
    
    if load_level == "high":
        return 1  # Single commit batches when overloaded
    elif load_level == "degraded":
        return 2  # Small batches when degraded
    elif total_commits > 50:
        return 3  # Larger batches for big analysis
    elif total_commits > 20:
        return 2  # Medium batches for medium analysis
    else:
        return 1  # Single commits for small analysis


def main():
    parser = argparse.ArgumentParser(
        description="Analyze git history and summarize changes"
    )
    parser.add_argument(
        "--since", help="Start date (e.g., '2024-01-01' or '2 days ago')"
    )
    parser.add_argument("--until", help="End date (e.g., '2024-01-31')")
    parser.add_argument(
        "--max-commits",
        type=int,
        default=20,
        help="Maximum number of commits to analyze",
    )
    parser.add_argument("--author", help="Filter by author")
    parser.add_argument(
        "--include-diff",
        action="store_true",
        default=True,
        help="Include full diff in output",
    )
    parser.add_argument(
        "--no-diff",
        dest="include_diff",
        action="store_false",
        help="Exclude diff from output",
    )
    parser.add_argument(
        "--summarize", action="store_true", default=True, help="Generate LLM summaries"
    )
    parser.add_argument(
        "--no-summarize",
        dest="summarize",
        action="store_false",
        help="Skip LLM summarization",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of commits to process before pausing",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "text", "story", "summary"],
        default="json",
        help="Output format",
    )
    parser.add_argument("--output-file", help="Output file (default: stdout)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be analyzed without processing",
    )

    args = parser.parse_args()

    # Get commit list
    logger.info("Fetching commit list...")
    logger.info(
        f"Arguments: since={args.since}, until={args.until}, max_commits={args.max_commits}, author={args.author}"
    )
    commits = get_commit_list(
        since=args.since,
        until=args.until,
        max_commits=args.max_commits,
        author=args.author,
    )

    if not commits:
        logger.error("No commits found matching criteria")
        sys.exit(1)

    logger.info(f"Found {len(commits)} commits to analyze")

    if args.dry_run:
        print("DRY RUN - Would analyze the following commits:")
        for commit in commits:
            print(f"  {commit.commit_hash[:8]} - {commit.author} - {commit.message}")
        return

    # Check LLM service health if summarization is enabled
    if args.summarize:
        if not check_llm_service_health():
            logger.error("❌ LLM service is not available. Cannot proceed with summarization.")
            logger.error("Options:")
            logger.error("  1. Start the ollama-functions service")
            logger.error("  2. Run with --no-summarize to skip LLM processing")
            logger.error("  3. Wait for the service to become available and retry")
            sys.exit(1)

    # Analyze commits
    logger.info("Starting commit analysis...")
    try:
        # Use adaptive batch size if not explicitly specified
        if args.batch_size == DEFAULT_BATCH_SIZE:
            health_data = check_ollama_health()
            adaptive_batch_size = get_adaptive_batch_size(len(commits), health_data)
            logger.info(f"Using adaptive batch size: {adaptive_batch_size} (based on {len(commits)} commits)")
            batch_size = adaptive_batch_size
        else:
            batch_size = args.batch_size
            
        analyzed_commits = analyze_commit_range(
            commits,
            include_diff=args.include_diff,
            summarize=args.summarize,
            batch_size=batch_size,
            health_data=health_data,
        )
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

    # Generate report
    logger.info("Generating report...")
    report = generate_report(analyzed_commits, args.output_format)

    # Output
    if args.output_file:
        with open(args.output_file, "w") as f:
            f.write(report)
        logger.info(f"Report written to {args.output_file}")
    else:
        print(report)


if __name__ == "__main__":
    main()

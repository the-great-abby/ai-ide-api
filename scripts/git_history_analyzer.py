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
from typing import Dict, List, Optional, Any
import requests
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("git_history_analyzer")

# Configuration
OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://api:8000/summarize-git-diff" if os.environ.get("RUNNING_IN_DOCKER") else "http://localhost:9103/summarize-git-diff"
)

class GitCommit:
    """Represents a single git commit with metadata."""
    
    def __init__(self, commit_hash: str, author: str, date: str, message: str, files_changed: List[str]):
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
            "tags": self.tags
        }

def get_commit_list(since: Optional[str] = None, until: Optional[str] = None, 
                   max_commits: int = 50, author: Optional[str] = None) -> List[GitCommit]:
    """Get a list of commits with metadata."""
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
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        i = 0
        while i < len(lines):
            if not lines[i].strip():
                i += 1
                continue
                
            # Parse commit line
            parts = lines[i].split('|')
            if len(parts) != 4:
                i += 1
                continue
                
            commit_hash, author, date, message = parts
            
            # Parse changed files
            files_changed = []
            i += 1
            while i < len(lines) and lines[i].strip() and not '|' in lines[i]:
                files_changed.append(lines[i].strip())
                i += 1
            
            commit = GitCommit(commit_hash, author, date, message, files_changed)
            commits.append(commit)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Git log failed: {e}")
        return []
    
    return commits

def get_commit_diff(commit_hash: str, parent_hash: Optional[str] = None) -> str:
    """Get the diff for a specific commit."""
    try:
        if parent_hash:
            cmd = ["git", "diff", parent_hash, commit_hash]
        else:
            cmd = ["git", "show", commit_hash, "--no-pager"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Git diff failed for {commit_hash}: {e}")
        return ""

def get_parent_commit(commit_hash: str) -> Optional[str]:
    """Get the parent commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", f"{commit_hash}^"], 
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def summarize_diff(diff: str, commit_message: str, author: str, concise: bool = True) -> Dict[str, Any]:
    """Summarize a git diff using the LLM service."""
    if not diff.strip():
        return {"summary": "No changes detected", "categories": [], "tags": []}
    
    try:
        payload = {
            "diff": diff,
            "commit_msg": commit_message,
            "author": author,
            "concise": concise
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract categories and tags if available
        categories = result.get("categories", [])
        tags = result.get("tags", [])
        summary = result.get("combined", result.get("summary", "No summary available"))
        
        return {
            "summary": summary,
            "categories": categories,
            "tags": tags
        }
        
    except Exception as e:
        logger.error(f"Failed to summarize diff: {e}")
        return {
            "summary": f"Error summarizing diff: {e}",
            "categories": [],
            "tags": []
        }

def analyze_commit(commit: GitCommit, include_diff: bool = True, summarize: bool = True) -> GitCommit:
    """Analyze a single commit by getting its diff and summary."""
    logger.info(f"Analyzing commit {commit.commit_hash[:8]} by {commit.author}")
    
    # Get parent commit
    parent_hash = get_parent_commit(commit.commit_hash)
    
    # Get diff
    if include_diff:
        commit.diff = get_commit_diff(commit.commit_hash, parent_hash)
    
    # Summarize if requested
    if summarize and commit.diff:
        summary_result = summarize_diff(
            commit.diff, 
            commit.message, 
            commit.author,
            concise=True
        )
        commit.summary = summary_result["summary"]
        commit.categories = summary_result["categories"]
        commit.tags = summary_result["tags"]
    
    return commit

def analyze_commit_range(commits: List[GitCommit], include_diff: bool = True, 
                        summarize: bool = True, batch_size: int = 5) -> List[GitCommit]:
    """Analyze a range of commits with optional batching."""
    analyzed_commits = []
    
    for i, commit in enumerate(commits):
        logger.info(f"Processing commit {i+1}/{len(commits)}: {commit.commit_hash[:8]}")
        
        analyzed_commit = analyze_commit(commit, include_diff, summarize)
        analyzed_commits.append(analyzed_commit)
        
        # Add delay between batches to avoid overwhelming the LLM service
        if (i + 1) % batch_size == 0 and i < len(commits) - 1:
            logger.info(f"Processed {i+1} commits, pausing...")
            time.sleep(2)
    
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
                "end": commits[0].date if commits else None
            }
        }
        
        return json.dumps(summary, indent=2)
    
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

def main():
    parser = argparse.ArgumentParser(description="Analyze git history and summarize changes")
    parser.add_argument("--since", help="Start date (e.g., '2024-01-01' or '2 days ago')")
    parser.add_argument("--until", help="End date (e.g., '2024-01-31')")
    parser.add_argument("--max-commits", type=int, default=20, help="Maximum number of commits to analyze")
    parser.add_argument("--author", help="Filter by author")
    parser.add_argument("--include-diff", action="store_true", default=True, help="Include full diff in output")
    parser.add_argument("--no-diff", dest="include_diff", action="store_false", help="Exclude diff from output")
    parser.add_argument("--summarize", action="store_true", default=True, help="Generate LLM summaries")
    parser.add_argument("--no-summarize", dest="summarize", action="store_false", help="Skip LLM summarization")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of commits to process before pausing")
    parser.add_argument("--output-format", choices=["json", "text", "summary"], default="json", 
                       help="Output format")
    parser.add_argument("--output-file", help="Output file (default: stdout)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be analyzed without processing")
    
    args = parser.parse_args()
    
    # Get commit list
    logger.info("Fetching commit list...")
    commits = get_commit_list(
        since=args.since,
        until=args.until,
        max_commits=args.max_commits,
        author=args.author
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
    
    # Analyze commits
    logger.info("Starting commit analysis...")
    analyzed_commits = analyze_commit_range(
        commits,
        include_diff=args.include_diff,
        summarize=args.summarize,
        batch_size=args.batch_size
    )
    
    # Generate report
    logger.info("Generating report...")
    report = generate_report(analyzed_commits, args.output_format)
    
    # Output
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(report)
        logger.info(f"Report written to {args.output_file}")
    else:
        print(report)

if __name__ == "__main__":
    main() 
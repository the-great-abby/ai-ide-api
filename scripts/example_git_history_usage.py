#!/usr/bin/env python3
"""
Example usage of the Git History Analyzer
Demonstrates different ways to analyze git history and generate reports.
"""

import json
import sys
import os

# Add the current directory to the path so we can import the analyzer
sys.path.insert(0, os.path.dirname(__file__))

from git_history_analyzer import (
    get_commit_list, 
    analyze_commit_range, 
    generate_report,
    GitCommit
)

def example_basic_analysis():
    """Basic example: Analyze last 5 commits."""
    print("=== Basic Analysis Example ===")
    
    # Get last 5 commits
    commits = get_commit_list(max_commits=5)
    
    if not commits:
        print("No commits found!")
        return
    
    print(f"Found {len(commits)} commits to analyze")
    
    # Analyze them (without LLM summarization for speed)
    analyzed_commits = analyze_commit_range(
        commits, 
        include_diff=True, 
        summarize=False,  # Skip LLM for this example
        batch_size=2
    )
    
    # Generate a text report
    report = generate_report(analyzed_commits, "text")
    print(report)

def example_author_analysis():
    """Example: Analyze commits by a specific author."""
    print("\n=== Author Analysis Example ===")
    
    # Get commits by a specific author (replace with actual author name)
    commits = get_commit_list(since="1 month ago", author="Your Name", max_commits=10)
    
    if not commits:
        print("No commits found for the specified author!")
        return
    
    print(f"Found {len(commits)} commits by the specified author")
    
    # Generate a summary report
    analyzed_commits = analyze_commit_range(
        commits, 
        include_diff=False,  # Skip diffs for summary
        summarize=False,
        batch_size=5
    )
    
    summary = generate_report(analyzed_commits, "summary")
    print(json.dumps(json.loads(summary), indent=2))

def example_time_period_analysis():
    """Example: Analyze commits from a specific time period."""
    print("\n=== Time Period Analysis Example ===")
    
    # Get commits from last week
    commits = get_commit_list(since="1 week ago", max_commits=15)
    
    if not commits:
        print("No commits found in the specified time period!")
        return
    
    print(f"Found {len(commits)} commits in the last week")
    
    # Generate JSON report
    analyzed_commits = analyze_commit_range(
        commits, 
        include_diff=True,
        summarize=False,
        batch_size=3
    )
    
    json_report = generate_report(analyzed_commits, "json")
    
    # Save to file
    with open("weekly_analysis.json", "w") as f:
        f.write(json_report)
    
    print("JSON report saved to weekly_analysis.json")

def example_custom_analysis():
    """Example: Custom analysis with specific criteria."""
    print("\n=== Custom Analysis Example ===")
    
    # Get commits with custom criteria
    commits = get_commit_list(
        since="2 weeks ago",
        until="1 day ago",
        max_commits=20
    )
    
    if not commits:
        print("No commits found matching criteria!")
        return
    
    print(f"Found {len(commits)} commits matching criteria")
    
    # Custom processing: filter commits with specific file types
    python_commits = []
    for commit in commits:
        python_files = [f for f in commit.files_changed if f.endswith('.py')]
        if python_files:
            commit.files_changed = python_files  # Only keep Python files
            python_commits.append(commit)
    
    print(f"Found {len(python_commits)} commits with Python file changes")
    
    # Analyze Python-related commits
    analyzed_commits = analyze_commit_range(
        python_commits,
        include_diff=True,
        summarize=False,
        batch_size=5
    )
    
    # Generate custom summary
    total_files = sum(len(c.files_changed) for c in analyzed_commits)
    authors = set(c.author for c in analyzed_commits)
    
    custom_summary = {
        "python_commits": len(analyzed_commits),
        "total_python_files_changed": total_files,
        "authors": list(authors),
        "date_range": {
            "start": analyzed_commits[-1].date if analyzed_commits else None,
            "end": analyzed_commits[0].date if analyzed_commits else None
        }
    }
    
    print("Custom Python Analysis Summary:")
    print(json.dumps(custom_summary, indent=2))

def example_dry_run():
    """Example: Dry run to see what would be analyzed."""
    print("\n=== Dry Run Example ===")
    
    # Get commits without processing
    commits = get_commit_list(since="3 days ago", max_commits=10)
    
    if not commits:
        print("No commits found!")
        return
    
    print("DRY RUN - Would analyze the following commits:")
    for i, commit in enumerate(commits, 1):
        print(f"  {i}. {commit.commit_hash[:8]} - {commit.author} - {commit.message}")
        print(f"     Files: {len(commit.files_changed)} files")
        if commit.files_changed:
            print(f"     Sample files: {', '.join(commit.files_changed[:3])}")
        print()

def main():
    """Run all examples."""
    print("Git History Analyzer Examples")
    print("=" * 50)
    
    try:
        example_basic_analysis()
        example_author_analysis()
        example_time_period_analysis()
        example_custom_analysis()
        example_dry_run()
        
        print("\n" + "=" * 50)
        print("All examples completed!")
        print("\nTo run the full analyzer with LLM summarization:")
        print("  python3 scripts/git_history_analyzer.py --since '1 week ago' --max-commits 10")
        print("\nOr use the Makefile target:")
        print("  make -f Makefile.ai misc-git-history-analyze SINCE='1 week ago' MAX_COMMITS=10")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
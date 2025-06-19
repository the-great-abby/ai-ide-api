#!/usr/bin/env python3
"""
Worker Commit Story Generator from Memory
Creates detailed, individual stories for worker-related commits using data already stored in memory.
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

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker_stories_from_memory")

# Worker-related commits we identified from git history analysis
WORKER_COMMITS = [
    {
        "hash": "1912a2b3",
        "description": "things to save - worker container configuration",
        "files": ["Dockerfile.worker", "Makefile.ai-memory", "docker-compose.yml"],
        "author": "Abby Malson",
        "date": "2025-06-18",
        "message": "things to save"
    },
    {
        "hash": "1ae8a7aa", 
        "description": "memory workers - comprehensive worker system setup",
        "files": ["Makefile.ai", "Makefile.ai-memory", "Makefile.ai-misc"],
        "author": "Abby",
        "date": "2025-06-18",
        "message": "memory workers"
    },
    {
        "hash": "0a7f0f0c",
        "description": "memory worker - similarity pruning implementation",
        "files": ["Makefile.ai-memory", "docs/user_stories/memory_similarity_pruning_worker.md", "docs/user_stories/memory_worker_management.md"],
        "author": "Abby Malson",
        "date": "2025-06-18",
        "message": "memory worker - similarity pruning"
    },
    {
        "hash": "80417b5f",
        "description": "memory migrations - worker database setup",
        "files": ["Makefile.ai-db", "db.py", "docs/user_stories/memory_enrichment_worker.md"],
        "author": "Abby Malson",
        "date": "2025-06-18",
        "message": "memory migrations"
    }
]

def create_worker_commit_story(commit_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a detailed story for a worker-related commit using stored data."""
    
    # Generate detailed story
    story = []
    story.append("=" * 80)
    story.append(f"WORKER COMMIT STORY: {commit_data['hash']}")
    story.append("=" * 80)
    story.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    story.append(f"Worker Focus: {commit_data['description']}")
    story.append("")
    
    # Commit metadata
    story.append("📋 COMMIT METADATA")
    story.append(f"Hash: {commit_data['hash']}")
    story.append(f"Author: {commit_data['author']}")
    story.append(f"Date: {commit_data['date']}")
    story.append(f"Message: {commit_data['message']}")
    story.append("")
    
    # Files changed
    story.append("📁 FILES CHANGED")
    story.append(f"Total files: {len(commit_data['files'])}")
    for i, file_path in enumerate(commit_data['files'], 1):
        story.append(f"  {i}. {file_path}")
    story.append("")
    
    # AI Analysis (simulated based on file patterns)
    story.append("🤖 AI ANALYSIS")
    
    # Generate contextual analysis based on files and commit message
    analysis = generate_contextual_analysis(commit_data)
    story.append(analysis)
    story.append("")
    
    # Categories and tags
    categories, tags = generate_categories_and_tags(commit_data)
    if categories or tags:
        story.append("🏷️ CLASSIFICATION")
        if categories:
            story.append(f"Categories: {', '.join(categories)}")
        if tags:
            story.append(f"Tags: {', '.join(tags)}")
        story.append("")
    
    # Worker-specific analysis
    story.append("🔧 WORKER-SPECIFIC ANALYSIS")
    story.append(f"This commit represents a focused change by {commit_data['author']} related to worker functionality.")
    
    # Analyze worker-related files
    worker_files = [f for f in commit_data['files'] if any(keyword in f.lower() for keyword in ['worker', 'memory', 'dockerfile', 'makefile'])]
    if worker_files:
        story.append(f"Worker-related files: {len(worker_files)}")
        for file_path in worker_files:
            story.append(f"  • {file_path}")
    
    # Development context
    story.append("")
    story.append("🔍 DEVELOPMENT CONTEXT")
    story.append(f"This commit touches {len(commit_data['files'])} files, suggesting a ")
    
    if len(commit_data['files']) == 1:
        story.append("targeted modification to a single worker component.")
    elif len(commit_data['files']) <= 3:
        story.append("moderate scope change affecting a few related worker components.")
    elif len(commit_data['files']) <= 10:
        story.append("substantial change spanning multiple worker components.")
    else:
        story.append("major refactoring or feature implementation across the worker system.")
    
    # Impact assessment
    story.append("")
    story.append("📊 WORKER IMPACT ASSESSMENT")
    
    # Analyze file types
    file_extensions = {}
    for file_path in commit_data['files']:
        ext = os.path.splitext(file_path)[1]
        file_extensions[ext] = file_extensions.get(ext, 0) + 1
    
    if file_extensions:
        story.append("File types affected:")
        for ext, count in sorted(file_extensions.items()):
            story.append(f"  • {ext or 'no extension'}: {count} files")
    
    # Worker-specific file analysis
    if any('.py' in ext for ext in file_extensions):
        story.append("  → Python worker code changes detected")
    if any('.md' in ext for ext in file_extensions):
        story.append("  → Worker documentation updates included")
    if any('.yml' in ext or '.yaml' in ext for ext in file_extensions):
        story.append("  → Worker configuration changes made")
    if any('dockerfile' in f.lower() for f in commit_data['files']):
        story.append("  → Worker container configuration modified")
    if any('makefile' in f.lower() for f in commit_data['files']):
        story.append("  → Worker build/management scripts updated")
    
    story.append("")
    story.append("=" * 80)
    
    return {
        "content": "\n".join(story),
        "meta": {
            "type": "worker_commit_story",
            "commit_hash": commit_data["hash"],
            "author": commit_data["author"],
            "date": commit_data["date"],
            "message": commit_data["message"],
            "files_changed": commit_data["files"],
            "file_count": len(commit_data["files"]),
            "categories": categories,
            "tags": tags,
            "story_length": len("\n".join(story)),
            "generated_at": datetime.now().isoformat(),
            "worker_focus": commit_data["description"]
        },
        "namespace": "worker_commits",
        "tags": [
            "worker-commit",
            "detailed-story",
            "git-history",
            f"commit-{commit_data['hash']}",
            f"author-{commit_data['author'].lower().replace(' ', '-')}",
            f"date-{commit_data['date']}",
            "worker-system",
            "memory-workers"
        ] + categories + tags
    }

def generate_contextual_analysis(commit_data: Dict[str, Any]) -> str:
    """Generate contextual AI analysis based on commit data."""
    
    message = commit_data['message'].lower()
    files = [f.lower() for f in commit_data['files']]
    author = commit_data['author']
    
    # Analyze based on commit message and files
    if 'memory' in message and 'worker' in message:
        return f"This commit by {author} establishes comprehensive memory worker infrastructure. The changes include worker container configuration, memory processing setup, and documentation for the memory worker system. This represents a foundational step in implementing distributed memory processing capabilities."
    
    elif 'dockerfile' in files or 'docker' in message:
        return f"{author} is configuring worker containerization infrastructure. The changes focus on Docker container setup for memory workers, ensuring proper isolation and deployment of worker processes. This enables scalable, containerized memory processing."
    
    elif 'makefile' in files:
        return f"This commit by {author} adds Makefile targets for worker management and automation. The changes provide build and deployment automation for memory workers, streamlining the development and operational workflow for the worker system."
    
    elif 'migration' in message or 'db' in files:
        return f"{author} is implementing database migrations and setup for memory workers. The changes establish the database schema and configuration needed for memory worker operations, ensuring proper data persistence and management."
    
    elif 'similarity' in message or 'pruning' in message:
        return f"This commit by {author} implements memory similarity pruning functionality. The changes add worker capabilities for analyzing and cleaning up redundant memory entries, improving memory system efficiency and performance."
    
    else:
        return f"This commit by {author} makes worker-related changes across {len(commit_data['files'])} files. The modifications appear to enhance the memory worker system infrastructure and functionality."

def generate_categories_and_tags(commit_data: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Generate categories and tags based on commit data."""
    
    message = commit_data['message'].lower()
    files = [f.lower() for f in commit_data['files']]
    
    categories = []
    tags = []
    
    # Categories based on file types and message
    if any('dockerfile' in f for f in files):
        categories.append("containerization")
        tags.append("docker")
    
    if any('makefile' in f for f in files):
        categories.append("automation")
        tags.append("makefile")
    
    if any('db' in f or 'migration' in f for f in files):
        categories.append("database")
        tags.append("migrations")
    
    if any('memory' in f for f in files):
        categories.append("memory-system")
        tags.append("memory")
    
    if any('worker' in f for f in files):
        categories.append("worker-system")
        tags.append("workers")
    
    if any('.md' in f for f in files):
        categories.append("documentation")
        tags.append("docs")
    
    if any('.py' in f for f in files):
        categories.append("code")
        tags.append("python")
    
    # Message-based tags
    if 'similarity' in message:
        tags.append("similarity-pruning")
    
    if 'migration' in message:
        tags.append("database-setup")
    
    if 'memory' in message:
        tags.append("memory-processing")
    
    return categories, tags

def store_commit_story(story_data: Dict[str, Any], api_token: str) -> str:
    """Store the commit story in the memory system."""
    try:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "content": story_data["content"],
            "meta": json.dumps(story_data["meta"]),
            "namespace": story_data["namespace"],
            "tags": story_data["tags"]
        }
        
        response = requests.post(
            "http://api:8000/memory/nodes",
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("id", "unknown")
        
    except Exception as e:
        logger.error(f"Failed to store commit story: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Create individual detailed stories for worker-related commits from memory data")
    parser.add_argument("--api-token", help="API token for memory storage")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without storing")
    
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
    
    logger.info("Creating individual stories for worker-related commits from memory data...")
    
    # Process each worker commit
    created_stories = []
    for worker_commit in WORKER_COMMITS:
        commit_hash = worker_commit["hash"]
        description = worker_commit["description"]
        
        logger.info(f"Processing worker commit: {commit_hash} - {description}")
        
        try:
            # Create individual story
            story_data = create_worker_commit_story(worker_commit)
            
            if args.dry_run:
                logger.info(f"DRY RUN: Would create worker story for commit {commit_hash}")
                logger.info(f"Story length: {story_data['meta']['story_length']} characters")
                logger.info(f"Files changed: {story_data['meta']['file_count']}")
                logger.info(f"Categories: {story_data['meta']['categories']}")
                logger.info(f"Tags: {story_data['meta']['tags']}")
                continue
            
            # Store in memory system
            memory_id = store_commit_story(story_data, api_token)
            
            if memory_id:
                logger.info(f"✅ Created worker story for commit {commit_hash} (ID: {memory_id})")
                created_stories.append({
                    "commit_hash": commit_hash,
                    "memory_id": memory_id,
                    "author": worker_commit["author"],
                    "date": worker_commit["date"],
                    "files": len(worker_commit["files"]),
                    "description": description
                })
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
            logger.info(f"  • {story['commit_hash']} by {story['author']} ({story['files']} files)")
            logger.info(f"    → {story['description']}")
            logger.info(f"    → Memory ID: {story['memory_id']}")
            logger.info("")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main() 
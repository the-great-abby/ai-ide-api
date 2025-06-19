#!/usr/bin/env python3
"""
Git History Analysis Worker
Processes git history analysis jobs from RabbitMQ queue.
Integrates with the existing worker infrastructure and memory system.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from git_history_analyzer import (
    get_commit_list, 
    analyze_commit_range, 
    generate_report,
    GitCommit
)
from utils.message_broker import RealRabbitMQClient, MessageBrokerBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("git_history_worker")

# Configuration
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
QUEUE_NAME = "git.history.analysis"
MEMORY_API_URL = os.environ.get("MEMORY_API_URL", "http://api:8000/memory")
MEMORY_API_TOKEN = os.environ.get("MEMORY_API_TOKEN", "")

def get_api_token() -> str:
    """Get API token from file or environment."""
    token_file = "/code/.apitoken"
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return MEMORY_API_TOKEN

def create_memory_node(content: str, meta: Dict[str, Any], namespace: str) -> Optional[str]:
    """Create a memory node with the analysis results."""
    import requests
    import json
    
    headers = {"Authorization": f"Bearer {get_api_token()}"}
    payload = {
        "namespace": namespace,
        "content": content,
        "meta": json.dumps(meta)  # Convert meta dict to JSON string
    }
    
    try:
        response = requests.post(f"{MEMORY_API_URL}/nodes", json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result.get("id")
    except Exception as e:
        logger.error(f"Failed to create memory node: {e}")
        return None

async def process_git_history_analysis_job(job_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a git history analysis job with the following config options:
    - since: str (e.g., '1 week ago', '2024-01-01')
    - until: str (optional)
    - max_commits: int (default: 20)
    - author: str (optional)
    - include_diff: bool (default: True)
    - summarize: bool (default: True)
    - output_format: str (json, text, summary)
    - create_memory_node: bool (default: False)
    - memory_namespace: str (default: 'git_history')
    - memory_tags: list (optional)
    """
    logger.info(f"=== GIT HISTORY WORKER STARTED ===")
    logger.info(f"Job config received: {job_config}")
    
    stats = {
        "commits_found": 0,
        "commits_analyzed": 0,
        "analysis_duration": 0,
        "memory_node_created": False,
        "start_time": asyncio.get_event_loop().time()
    }
    
    try:
        logger.info(f"Starting git history analysis job: {job_config}")
        
        # Extract job parameters
        since = job_config.get("since")
        until = job_config.get("until")
        max_commits = job_config.get("max_commits", 20)
        author = job_config.get("author")
        include_diff = job_config.get("include_diff", True)
        summarize = job_config.get("summarize", True)
        output_format = job_config.get("output_format", "json")
        create_memory = job_config.get("create_memory_node", False)
        memory_namespace = job_config.get("memory_namespace", "git_history")
        memory_tags = job_config.get("memory_tags", [])
        
        # Get commit list
        logger.info(f"Fetching commits since: {since}, until: {until}, max: {max_commits}")
        commits = get_commit_list(
            since=since,
            until=until,
            max_commits=max_commits,
            author=author
        )
        
        if not commits:
            logger.info("No commits found matching criteria")
            return {
                "status": "success",
                "message": "No commits found matching criteria",
                "stats": stats
            }
        
        stats["commits_found"] = len(commits)
        logger.info(f"Found {len(commits)} commits to analyze")
        
        # Analyze commits
        logger.info("Starting commit analysis...")
        analyzed_commits = analyze_commit_range(
            commits,
            include_diff=include_diff,
            summarize=summarize,
            batch_size=job_config.get("batch_size", 5)
        )
        
        stats["commits_analyzed"] = len(analyzed_commits)
        
        # Generate report
        logger.info(f"Generating {output_format} report...")
        report = generate_report(analyzed_commits, output_format)
        
        # Create memory node if requested
        if create_memory:
            logger.info("Creating memory node with analysis results...")
            
            # Prepare memory node content
            if output_format == "story":
                content = f"Development story: {report[:500]}..." if len(report) > 500 else report
            elif output_format == "summary":
                content = f"Git history analysis summary: {report}"
            elif output_format == "text":
                content = report[:1000] + "..." if len(report) > 1000 else report
            else:  # json
                content = f"Git history analysis completed. Found {len(analyzed_commits)} commits."
            
            # Prepare metadata
            meta = {
                "type": "git_history_analysis",
                "output_format": output_format,
                "since": since,
                "until": until,
                "max_commits": max_commits,
                "author": author,
                "commits_analyzed": len(analyzed_commits),
                "tags": memory_tags + ["git-history", "analysis"],
                "categories": ["development", "code-analysis"],
                "full_report": report if output_format != "json" else None,
                "report_length": len(report),
                "story_mode": output_format == "story"
            }
            
            # Create the memory node
            memory_id = create_memory_node(content, meta, memory_namespace)
            if memory_id:
                stats["memory_node_created"] = True
                logger.info(f"Created memory node with ID: {memory_id}")
            else:
                logger.warning("Failed to create memory node")
        
        stats["analysis_duration"] = asyncio.get_event_loop().time() - stats["start_time"]
        
        return {
            "status": "success",
            "report": report,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Git history analysis job failed: {e}")
        stats["analysis_duration"] = asyncio.get_event_loop().time() - stats["start_time"]
        return {
            "status": "error",
            "error": str(e),
            "stats": stats
        }

async def main():
    """Main worker loop."""
    broker = RealRabbitMQClient(RABBITMQ_URL)
    logger.info("Git History Analysis Worker started, polling for jobs...")
    
    while True:
        try:
            body = await broker.consume(QUEUE_NAME)
            if body:
                logger.info(f"Received job: {body}")
                try:
                    result = await process_git_history_analysis_job(body)
                    logger.info(f"Job completed with status: {result['status']}")
                    if result.get("stats"):
                        stats = result["stats"]
                        logger.info(f"Stats: {stats['commits_analyzed']} commits analyzed in {stats['analysis_duration']:.2f}s")
                except Exception as e:
                    logger.error(f"Error processing job: {e}")
            else:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main()) 
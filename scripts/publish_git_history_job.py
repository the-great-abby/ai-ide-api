#!/usr/bin/env python3
"""
Publish Git History Analysis Job
Publishes git history analysis jobs to RabbitMQ queue.
"""

import argparse
import json
import asyncio
import os
from utils.message_broker import RealRabbitMQClient, MessageBrokerBase

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
QUEUE_NAME = "git.history.analysis"

async def publish_git_history_job(job_config: dict, broker: MessageBrokerBase = None):
    """Publish a git history analysis job to RabbitMQ."""
    if broker is None:
        broker = RealRabbitMQClient(RABBITMQ_URL)
    
    await broker.publish(QUEUE_NAME, job_config)
    print(f"Published git history analysis job: {json.dumps(job_config, indent=2)}")

def main():
    parser = argparse.ArgumentParser(description="Publish git history analysis job to RabbitMQ")
    parser.add_argument("--since", required=True, help="Start date (e.g., '1 week ago', '2024-01-01')")
    parser.add_argument("--until", help="End date (e.g., '1 day ago', '2024-01-31')")
    parser.add_argument("--max-commits", type=int, default=20, help="Maximum number of commits to analyze")
    parser.add_argument("--author", help="Filter by author")
    parser.add_argument("--include-diff", action="store_true", default=True, help="Include full diff in output")
    parser.add_argument("--no-diff", dest="include_diff", action="store_false", help="Exclude diff from output")
    parser.add_argument("--summarize", action="store_true", default=True, help="Generate LLM summaries")
    parser.add_argument("--no-summarize", dest="summarize", action="store_false", help="Skip LLM summarization")
    parser.add_argument("--output-format", choices=["json", "text", "summary"], default="json", 
                       help="Output format")
    parser.add_argument("--create-memory-node", action="store_true", help="Create memory node with results")
    parser.add_argument("--memory-namespace", default="git_history_analysis", help="Memory namespace")
    parser.add_argument("--memory-tags", nargs="*", default=[], help="Additional memory tags")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of commits to process before pausing")
    
    args = parser.parse_args()
    
    # Build job configuration
    job_config = {
        "since": args.since,
        "max_commits": args.max_commits,
        "include_diff": args.include_diff,
        "summarize": args.summarize,
        "output_format": args.output_format,
        "create_memory_node": args.create_memory_node,
        "memory_namespace": args.memory_namespace,
        "memory_tags": args.memory_tags,
        "batch_size": args.batch_size
    }
    
    if args.until:
        job_config["until"] = args.until
    
    if args.author:
        job_config["author"] = args.author
    
    # Publish job
    asyncio.run(publish_git_history_job(job_config))
    print("Job published successfully!")

if __name__ == "__main__":
    main() 
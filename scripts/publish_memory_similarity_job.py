#!/usr/bin/env python3
"""
Publish a memory similarity pruning job to RabbitMQ.
This script helps schedule similarity detection and pruning tasks.

Example usage:
    # Process all nodes
    python scripts/publish_memory_similarity_job.py --scope all

    # Process new nodes only
    python scripts/publish_memory_similarity_job.py --scope new --dry-run

    # Process specific namespace
    python scripts/publish_memory_similarity_job.py --scope namespace:docs --vector-threshold 0.95
"""
import os
import sys
import json
import asyncio
import argparse
from utils.message_broker import RealRabbitMQClient

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
QUEUE_NAME = "memory.similarity"

async def publish_job(args):
    """Publish a similarity pruning job to RabbitMQ."""
    # Prepare job configuration
    job_config = {
        "scope": args.scope,
        "dry_run": args.dry_run,
    }
    
    # Add optional thresholds if specified
    if args.vector_threshold is not None:
        job_config["vector_similarity_threshold"] = args.vector_threshold
    if args.content_threshold is not None:
        job_config["content_similarity_threshold"] = args.content_threshold
    if args.tag_threshold is not None:
        job_config["tag_overlap_threshold"] = args.tag_threshold
        
    # Connect to RabbitMQ and publish
    try:
        broker = RealRabbitMQClient(RABBITMQ_URL)
        await broker.publish(QUEUE_NAME, job_config)
        print(f"Published similarity pruning job: {json.dumps(job_config, indent=2)}")
    except Exception as e:
        print(f"Error publishing job: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Publish a memory similarity pruning job")
    parser.add_argument(
        "--scope",
        choices=["all", "new"],
        default="all",
        help="Scope of nodes to process. Use 'namespace:xyz' for specific namespace."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report changes, don't apply them"
    )
    parser.add_argument(
        "--vector-threshold",
        type=float,
        help="Vector similarity threshold (0-1)"
    )
    parser.add_argument(
        "--content-threshold",
        type=float,
        help="Content similarity threshold (0-1)"
    )
    parser.add_argument(
        "--tag-threshold",
        type=float,
        help="Tag overlap threshold (0-1)"
    )
    
    args = parser.parse_args()
    
    # Allow namespace:xyz format
    if args.scope.startswith("namespace:"):
        if len(args.scope.split(":")) != 2:
            parser.error("Namespace format should be 'namespace:xyz'")
    
    # Validate thresholds
    for name, value in [
        ("vector", args.vector_threshold),
        ("content", args.content_threshold),
        ("tag", args.tag_threshold)
    ]:
        if value is not None and not (0 <= value <= 1):
            parser.error(f"{name} threshold must be between 0 and 1")
    
    asyncio.run(publish_job(args))

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Memory Enrichment Job Publisher

Publishes enrichment jobs to the memory.enrichment queue for processing.
Can be triggered manually or scheduled for nightly runs.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the current directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.message_broker import RealRabbitMQClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "scope": "all",
    "dry_run": False,
    "similarity_threshold": 0.85,
    "max_tags": 5,
    "batch_size": 50,
    "target_batch_tokens": 12000,
    "priority": "normal",
    "create_edges": True,  # Enable edge creation by default
    "edge_types": ["tag_based", "content_ref"]  # Types of edges to create
}

def create_enrichment_job(
    scope: str = "all",
    dry_run: bool = False,
    similarity_threshold: float = 0.85,
    max_tags: int = 5,
    batch_size: int = 50,
    target_batch_tokens: int = 12000,
    priority: str = "normal",
    create_edges: bool = True,
    edge_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create an enrichment job payload."""
    
    if edge_types is None:
        edge_types = ["tag_based", "content_ref"]
    
    job = {
        "scope": scope,
        "dry_run": dry_run,
        "similarity_threshold": similarity_threshold,
        "max_tags": max_tags,
        "batch_size": batch_size,
        "target_batch_tokens": target_batch_tokens,
        "priority": priority,
        "create_edges": create_edges,
        "edge_types": edge_types,
        "created_at": datetime.utcnow().isoformat(),
        "job_type": "memory_enrichment",
        "version": "1.1"  # Updated version for edge creation feature
    }
    
    return job

async def publish_enrichment_job(
    job_config: Dict[str, Any],
    rabbitmq_url: str = None
) -> bool:
    """Publish an enrichment job to the queue."""
    
    if rabbitmq_url is None:
        rabbitmq_url = os.environ.get(
            "RABBITMQ_URL", 
            "amqp://user:password@rabbitmq:5672/"
        )
    
    try:
        # Create RabbitMQ client
        broker = RealRabbitMQClient(rabbitmq_url)
        
        # Publish job to memory.enrichment queue
        await broker.publish("memory.enrichment", job_config)
        
        logger.info(f"Successfully published enrichment job: {job_config}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to publish enrichment job: {e}")
        return False

def main():
    """Main entry point for the script."""
    
    parser = argparse.ArgumentParser(
        description="Publish memory enrichment jobs"
    )
    parser.add_argument(
        "--scope",
        default="all",
        help="Scope of enrichment: 'all', 'new', or 'namespace:xyz'"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no actual changes)"
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.85,
        help="Similarity threshold for enrichment (0.0-1.0)"
    )
    parser.add_argument(
        "--max-tags",
        type=int,
        default=5,
        help="Maximum number of tags to extract per memory"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of memories to process per batch"
    )
    parser.add_argument(
        "--target-batch-tokens",
        type=int,
        default=12000,
        help="Target tokens per batch for LLM processing"
    )
    parser.add_argument(
        "--priority",
        default="normal",
        choices=["low", "normal", "high"],
        help="Job priority"
    )
    parser.add_argument(
        "--create-edges",
        action="store_true",
        default=True,
        help="Create edges between related nodes after enrichment"
    )
    parser.add_argument(
        "--no-create-edges",
        action="store_true",
        help="Disable edge creation"
    )
    parser.add_argument(
        "--edge-types",
        nargs="+",
        choices=["tag_based", "content_ref"],
        default=["tag_based", "content_ref"],
        help="Types of edges to create"
    )
    parser.add_argument(
        "--rabbitmq-url",
        help="RabbitMQ connection URL"
    )
    
    args = parser.parse_args()
    
    # Determine edge creation setting
    create_edges = args.create_edges and not args.no_create_edges
    
    # Create job configuration
    job_config = create_enrichment_job(
        scope=args.scope,
        dry_run=args.dry_run,
        similarity_threshold=args.similarity_threshold,
        max_tags=args.max_tags,
        batch_size=args.batch_size,
        target_batch_tokens=args.target_batch_tokens,
        priority=args.priority,
        create_edges=create_edges,
        edge_types=args.edge_types
    )
    
    logger.info(f"Publishing enrichment job with config: {json.dumps(job_config, indent=2)}")
    
    # Publish the job
    import asyncio
    success = asyncio.run(publish_enrichment_job(job_config, args.rabbitmq_url))
    
    if success:
        logger.info("✅ Enrichment job published successfully!")
        return 0
    else:
        logger.error("❌ Failed to publish enrichment job")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
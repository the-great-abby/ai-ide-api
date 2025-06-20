#!/usr/bin/env python3
"""
Memory Enrichment Nightly Scheduler

Runs memory enrichment jobs nightly between 10pm and 2am.
Can be run as a cron job or as a long-running service.
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from datetime import datetime, time as dt_time
from typing import Dict, Any

# Add the current directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from publish_memory_enrichment_job import create_enrichment_job, publish_enrichment_job

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Nightly schedule configuration
NIGHTLY_START_TIME = dt_time(22, 0)  # 10:00 PM
NIGHTLY_END_TIME = dt_time(2, 0)     # 2:00 AM

def is_nightly_window() -> bool:
    """Check if current time is within the nightly window (10pm-2am)."""
    now = datetime.now().time()
    
    # Handle the case where the window crosses midnight
    if NIGHTLY_START_TIME <= NIGHTLY_END_TIME:
        # Normal case: 10pm to 2am same day
        return NIGHTLY_START_TIME <= now <= NIGHTLY_END_TIME
    else:
        # Crosses midnight: 10pm to 2am next day
        return now >= NIGHTLY_START_TIME or now <= NIGHTLY_END_TIME

def get_seconds_until_nightly() -> int:
    """Calculate seconds until the next nightly window starts."""
    now = datetime.now()
    tonight_start = now.replace(
        hour=NIGHTLY_START_TIME.hour,
        minute=NIGHTLY_START_TIME.minute,
        second=0,
        microsecond=0
    )
    
    # If it's already past tonight's start time, schedule for tomorrow
    if now.time() >= NIGHTLY_START_TIME:
        tonight_start = tonight_start.replace(day=tonight_start.day + 1)
    
    return int((tonight_start - now).total_seconds())

async def run_nightly_enrichment(
    scope: str = "all",
    dry_run: bool = False,
    similarity_threshold: float = 0.85,
    max_tags: int = 5,
    batch_size: int = 50,
    target_batch_tokens: int = 12000,
    priority: str = "normal"
) -> bool:
    """Run the nightly enrichment job."""
    
    logger.info("🌙 Starting nightly memory enrichment job...")
    
    # Create job configuration
    job_config = create_enrichment_job(
        scope=scope,
        dry_run=dry_run,
        similarity_threshold=similarity_threshold,
        max_tags=max_tags,
        batch_size=batch_size,
        target_batch_tokens=target_batch_tokens,
        priority=priority
    )
    
    # Add nightly-specific metadata
    job_config["scheduled_run"] = True
    job_config["run_time"] = datetime.utcnow().isoformat()
    job_config["run_type"] = "nightly"
    
    # Publish the job
    success = await publish_enrichment_job(job_config)
    
    if success:
        logger.info("✅ Nightly enrichment job published successfully!")
    else:
        logger.error("❌ Failed to publish nightly enrichment job")
    
    return success

async def scheduler_loop(
    scope: str = "all",
    dry_run: bool = False,
    similarity_threshold: float = 0.85,
    max_tags: int = 5,
    batch_size: int = 50,
    target_batch_tokens: int = 12000,
    priority: str = "normal",
    check_interval: int = 300  # Check every 5 minutes
):
    """Main scheduler loop that runs continuously."""
    
    logger.info("🚀 Memory enrichment scheduler started")
    logger.info(f"📅 Nightly window: {NIGHTLY_START_TIME} - {NIGHTLY_END_TIME}")
    logger.info(f"⏰ Check interval: {check_interval} seconds")
    
    while True:
        try:
            now = datetime.now()
            logger.debug(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if is_nightly_window():
                logger.info("🌙 Nightly window is active - checking if enrichment should run...")
                
                # Check if we should run enrichment (avoid running multiple times in one night)
                # For now, we'll run once per night. In the future, we could add more sophisticated
                # logic to track when the last enrichment ran.
                
                success = await run_nightly_enrichment(
                    scope=scope,
                    dry_run=dry_run,
                    similarity_threshold=similarity_threshold,
                    max_tags=max_tags,
                    batch_size=batch_size,
                    target_batch_tokens=target_batch_tokens,
                    priority=priority
                )
                
                if success:
                    # Wait until the nightly window ends to avoid multiple runs
                    logger.info("⏳ Waiting for nightly window to end...")
                    while is_nightly_window():
                        await asyncio.sleep(60)  # Check every minute
                else:
                    # If failed, wait a bit before retrying
                    await asyncio.sleep(check_interval)
            else:
                # Outside nightly window, wait until next check
                seconds_until_nightly = get_seconds_until_nightly()
                logger.info(f"⏰ Outside nightly window. Next run in {seconds_until_nightly} seconds")
                
                # Sleep until next check or until nightly window starts
                sleep_time = min(check_interval, seconds_until_nightly)
                await asyncio.sleep(sleep_time)
                
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            await asyncio.sleep(check_interval)

def main():
    """Main entry point for the script."""
    
    parser = argparse.ArgumentParser(
        description="Memory enrichment nightly scheduler"
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
        "--check-interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300)"
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run enrichment immediately (ignore nightly window)"
    )
    
    args = parser.parse_args()
    
    if args.run_now:
        logger.info("🚀 Running enrichment job immediately...")
        success = asyncio.run(run_nightly_enrichment(
            scope=args.scope,
            dry_run=args.dry_run,
            similarity_threshold=args.similarity_threshold,
            max_tags=args.max_tags,
            batch_size=args.batch_size,
            target_batch_tokens=args.target_batch_tokens,
            priority=args.priority
        ))
        return 0 if success else 1
    else:
        logger.info("🕐 Starting scheduler loop...")
        asyncio.run(scheduler_loop(
            scope=args.scope,
            dry_run=args.dry_run,
            similarity_threshold=args.similarity_threshold,
            max_tags=args.max_tags,
            batch_size=args.batch_size,
            target_batch_tokens=args.target_batch_tokens,
            priority=args.priority,
            check_interval=args.check_interval
        ))

if __name__ == "__main__":
    sys.exit(main()) 
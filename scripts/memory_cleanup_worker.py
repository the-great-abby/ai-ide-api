#!/usr/bin/env python3
"""
Memory Cleanup Worker
Removes outdated, duplicate, or irrelevant memory nodes from the memorydb.
Follows the user story in docs/user_stories/memory_cleanup_worker.md.
"""
import argparse
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import json
import asyncio
from typing import Dict, Any

from db import MemorySessionLocal, MemoryVector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory_cleanup_worker")

# Criteria
default_age_days = 180  # Nodes older than this are considered stale


def parse_meta(meta_str):
    if not meta_str:
        return {}
    try:
        return json.loads(meta_str)
    except Exception:
        return {}

def find_duplicates(nodes):
    """Return sets of node IDs with duplicate content in the same namespace."""
    seen = defaultdict(list)
    for node in nodes:
        key = (node.namespace, node.content.strip())
        seen[key].append(node)
    duplicates = []
    for group in seen.values():
        if len(group) > 1:
            # Keep the newest, mark others as duplicates
            sorted_group = sorted(group, key=lambda n: n.created_at, reverse=True)
            duplicates.extend(sorted_group[1:])
    return duplicates

def find_deprecated(nodes):
    """Return nodes with meta indicating 'deprecated' or 'obsolete'."""
    flagged = []
    for node in nodes:
        meta = parse_meta(node.meta)
        status = meta.get("status", "").lower()
        if status in ("deprecated", "obsolete"):
            flagged.append(node)
    return flagged

def find_stale(nodes, age_days):
    """Return nodes older than age_days."""
    cutoff = datetime.utcnow() - timedelta(days=age_days)
    return [node for node in nodes if node.created_at < cutoff]

async def process_memory_cleanup_job(body: Dict[str, Any]):
    """
    Async handler for RabbitMQ jobs. Accepts a dict payload with options:
      - dry_run: bool
      - age_days: int
    """
    dry_run = body.get("dry_run", False)
    age_days = body.get("age_days", default_age_days)
    logger.info(f"[memory_cleanup_worker] Starting cleanup job (dry_run={dry_run}, age_days={age_days})")

    session = MemorySessionLocal()
    nodes = session.query(MemoryVector).all()
    logger.info(f"Loaded {len(nodes)} memory nodes from memorydb.")

    # Find candidates
    stale = find_stale(nodes, age_days)
    duplicates = find_duplicates(nodes)
    deprecated = find_deprecated(nodes)

    # Use sets of IDs to avoid double-counting
    to_delete = {n.id: n for n in stale + duplicates + deprecated}
    logger.info(f"Identified {len(stale)} stale, {len(duplicates)} duplicates, {len(deprecated)} deprecated/obsolete nodes.")
    logger.info(f"Total unique nodes to delete: {len(to_delete)}")

    # Log details
    for node in to_delete.values():
        logger.info(f"[CANDIDATE] id={node.id} ns={node.namespace} created={node.created_at} meta={node.meta}")

    if dry_run:
        logger.info("Dry run mode: no deletions performed.")
        session.close()
        return

    # Delete nodes
    deleted = 0
    for node in to_delete.values():
        session.delete(node)
        deleted += 1
    session.commit()
    session.close()
    logger.info(f"Deleted {deleted} memory nodes.")

# Retain CLI entrypoint for manual runs

def main():
    parser = argparse.ArgumentParser(description="Memory Cleanup Worker")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without deleting")
    parser.add_argument("--age-days", type=int, default=default_age_days, help="Age threshold for staleness")
    args = parser.parse_args()
    # Call the async handler from sync code
    asyncio.run(process_memory_cleanup_job({"dry_run": args.dry_run, "age_days": args.age_days}))

if __name__ == "__main__":
    main() 
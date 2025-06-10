#!/usr/bin/env python3
"""
Stale Rule Detector
Flags rules and memory nodes that are outdated, contradicted, or deprecated but not removed.
Follows the user story in docs/user_stories/stale_rule_detector.md.
"""
import argparse
import logging
import os
import json
from datetime import datetime, timedelta
from db import MemorySessionLocal, MemoryVector, SessionLocal, Rule

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stale_rule_detector")

# Criteria
DEFAULT_STALE_DAYS = 180  # Not updated in this many days is considered stale


def parse_meta(meta_str):
    if not meta_str:
        return {}
    try:
        return json.loads(meta_str)
    except Exception:
        return {}

def is_deprecated(meta):
    status = meta.get("status", "").lower()
    return status in ("deprecated", "obsolete")

def main():
    parser = argparse.ArgumentParser(description="Stale Rule Detector")
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS, help="Days since last update to consider stale")
    parser.add_argument("--dry-run", action="store_true", help="Preview flagged entries without taking action")
    args = parser.parse_args()

    cutoff = datetime.utcnow() - timedelta(days=args.stale_days)

    # Check memory nodes
    mem_session = MemorySessionLocal()
    mem_nodes = mem_session.query(MemoryVector).all()
    stale_mem = [n for n in mem_nodes if n.created_at < cutoff]
    deprecated_mem = [n for n in mem_nodes if is_deprecated(parse_meta(n.meta))]
    logger.info(f"Flagged {len(stale_mem)} stale memory nodes and {len(deprecated_mem)} deprecated/obsolete memory nodes.")
    for n in stale_mem:
        logger.info(f"[STALE MEMORY] id={n.id} ns={n.namespace} created={n.created_at} meta={n.meta}")
    for n in deprecated_mem:
        logger.info(f"[DEPRECATED MEMORY] id={n.id} ns={n.namespace} created={n.created_at} meta={n.meta}")
    mem_session.close()

    # Check rules
    rule_session = SessionLocal()
    rules = rule_session.query(Rule).all()
    stale_rules = [r for r in rules if r.timestamp and r.timestamp < cutoff]
    deprecated_rules = [r for r in rules if is_deprecated(parse_meta(getattr(r, 'meta', None)))]
    logger.info(f"Flagged {len(stale_rules)} stale rules and {len(deprecated_rules)} deprecated/obsolete rules.")
    for r in stale_rules:
        logger.info(f"[STALE RULE] id={r.id} desc={r.description[:80]}... timestamp={r.timestamp}")
    for r in deprecated_rules:
        logger.info(f"[DEPRECATED RULE] id={r.id} desc={r.description[:80]}...")
    rule_session.close()

    logger.info("Dry run: no issues opened or notifications sent. Review logs for flagged entries.")

if __name__ == "__main__":
    main() 
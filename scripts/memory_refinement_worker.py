#!/usr/bin/env python3
"""
Memory Refinement Worker
Improves and clarifies memory nodes using LLM summarization, clarification, and merge suggestions.
Follows the user story in docs/user_stories/memory_refinement_worker.md.
"""
import argparse
import logging
import os
import json
from datetime import datetime
from collections import defaultdict
from difflib import SequenceMatcher
import requests

from db import MemorySessionLocal, MemoryVector

# LLM config
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q6_K")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory_refinement_worker")

# Criteria
LONG_CONTENT_THRESHOLD = 500  # Characters
AMBIGUOUS_PHRASES = ["TBD", "unclear", "fixme", "???", "to be decided", "to be determined"]
MERGE_SIMILARITY_THRESHOLD = 0.85  # For merge suggestions


def call_ollama(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
    except Exception as e:
        logger.error(f"[ERROR] Ollama call failed: {e}")
        return None

def parse_meta(meta_str):
    if not meta_str:
        return {}
    try:
        return json.loads(meta_str)
    except Exception:
        return {}

def is_ambiguous(content, meta):
    content_lower = content.lower()
    if any(phrase in content_lower for phrase in AMBIGUOUS_PHRASES):
        return True
    status = meta.get("status", "").lower()
    if status in ("unclear", "ambiguous"):
        return True
    return False

def find_similar_nodes(nodes):
    """Suggest merges for nodes with high content similarity in the same namespace."""
    suggestions = []
    by_ns = defaultdict(list)
    for node in nodes:
        by_ns[node.namespace].append(node)
    for ns, group in by_ns.items():
        for i, n1 in enumerate(group):
            for n2 in group[i+1:]:
                ratio = SequenceMatcher(None, n1.content, n2.content).ratio()
                if ratio > MERGE_SIMILARITY_THRESHOLD:
                    suggestions.append((n1, n2, ratio))
    return suggestions

def main():
    parser = argparse.ArgumentParser(description="Memory Refinement Worker")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying them")
    parser.add_argument("--apply", action="store_true", help="Apply changes to the database")
    args = parser.parse_args()

    if args.dry_run and args.apply:
        logger.error("Cannot use --dry-run and --apply together.")
        return

    session = MemorySessionLocal()
    nodes = session.query(MemoryVector).all()
    logger.info(f"Loaded {len(nodes)} memory nodes from memorydb.")

    # Summarize long entries
    for node in nodes:
        if node.content and len(node.content) > LONG_CONTENT_THRESHOLD:
            prompt = (
                f"Summarize the following memory node content in 1-2 sentences, preserving all key details:\n\n{node.content}"
            )
            summary = call_ollama(prompt)
            if summary and summary.strip() != node.content.strip():
                logger.info(f"[SUMMARY] id={node.id} ns={node.namespace}\n  Original: {node.content[:100]}...\n  Summary: {summary[:100]}...")
                if args.apply:
                    meta = parse_meta(node.meta)
                    meta["original_content"] = node.content
                    node.content = summary.strip()
                    node.meta = json.dumps(meta)
    # Clarify ambiguous entries
    for node in nodes:
        meta = parse_meta(node.meta)
        if is_ambiguous(node.content, meta):
            prompt = (
                f"Rewrite the following memory node content to be clear and unambiguous. If information is missing, note it explicitly.\n\n{node.content}"
            )
            clarified = call_ollama(prompt)
            if clarified and clarified.strip() != node.content.strip():
                logger.info(f"[CLARIFY] id={node.id} ns={node.namespace}\n  Original: {node.content[:100]}...\n  Clarified: {clarified[:100]}...")
                if args.apply:
                    meta = parse_meta(node.meta)
                    meta["original_content"] = node.content
                    node.content = clarified.strip()
                    node.meta = json.dumps(meta)
    # Suggest merges for similar nodes
    merge_suggestions = find_similar_nodes(nodes)
    for n1, n2, ratio in merge_suggestions:
        logger.info(f"[MERGE SUGGESTION] ns={n1.namespace} id1={n1.id} id2={n2.id} similarity={ratio:.2f}")
        logger.info(f"  Content 1: {n1.content[:100]}...")
        logger.info(f"  Content 2: {n2.content[:100]}...")
    if args.apply:
        session.commit()
        logger.info("Applied all changes to the database.")
    else:
        logger.info("Dry run: no changes applied. Review logs for proposed refinements.")
    session.close()

if __name__ == "__main__":
    main() 
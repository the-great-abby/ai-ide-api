#!/usr/bin/env python3
"""
Memory Similarity Pruning Worker
Identifies and handles similar/duplicate memory nodes using multiple similarity measures:
1. Vector similarity (cosine distance between embeddings)
2. Content similarity (sequence matching)
3. Tag/category overlap
4. Namespace grouping

Follows best practices from memory_cleanup_worker.py and memory_enrichment_worker.py
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
import json
import time
from collections import defaultdict
from difflib import SequenceMatcher
import numpy as np
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from db import MemorySessionLocal, MemoryVector, MemoryEdge
from memory import call_ollama_llm, get_embedding_ollama

logger = logging.getLogger("memory_similarity_pruning_worker")
logging.basicConfig(level=logging.INFO)

# Constants
VECTOR_SIMILARITY_THRESHOLD = 0.92  # Cosine similarity threshold
CONTENT_SIMILARITY_THRESHOLD = 0.85  # Sequence matcher ratio threshold
TAG_OVERLAP_THRESHOLD = 0.7  # Minimum ratio of shared tags
MIN_CONTENT_LENGTH = 50  # Minimum content length to consider for similarity
BATCH_SIZE = 100  # Number of nodes to process at once


class SimilarityGroup:
    """Group of similar nodes with their similarity scores."""

    def __init__(self, primary_node: MemoryVector):
        self.primary = primary_node  # Keep newest node as primary
        self.similar: List[Tuple[MemoryVector, float]] = []  # (node, similarity_score)

    def add_node(self, node: MemoryVector, similarity: float):
        self.similar.append((node, similarity))

    @property
    def size(self) -> int:
        return len(self.similar) + 1

    def should_merge(self) -> bool:
        """Determine if this group should be automatically merged."""
        if not self.similar:
            return False
        # If any node has very high similarity, suggest merge
        return any(score > VECTOR_SIMILARITY_THRESHOLD for _, score in self.similar)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not v1 or not v2:
        return 0.0
    v1_arr = np.array(v1)
    v2_arr = np.array(v2)
    dot_product = np.dot(v1_arr, v2_arr)
    norm_v1 = np.linalg.norm(v1_arr)
    norm_v2 = np.linalg.norm(v2_arr)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)


def content_similarity(text1: str, text2: str) -> float:
    """Calculate content similarity using SequenceMatcher."""
    return SequenceMatcher(None, text1.strip(), text2.strip()).ratio()


def tag_similarity(tags1: List[str], tags2: List[str]) -> float:
    """Calculate similarity based on shared tags."""
    if not tags1 or not tags2:
        return 0.0
    set1 = set(tags1)
    set2 = set(tags2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


async def find_similar_nodes(nodes: List[MemoryVector]) -> List[SimilarityGroup]:
    """
    Find groups of similar nodes using multiple similarity measures.
    Returns list of SimilarityGroup objects.
    """
    # Group by namespace first
    by_namespace = defaultdict(list)
    for node in nodes:
        if len(node.content) >= MIN_CONTENT_LENGTH:
            by_namespace[node.namespace].append(node)

    similarity_groups = []

    # Process each namespace separately
    for namespace, ns_nodes in by_namespace.items():
        # Sort by creation date, newest first
        ns_nodes.sort(key=lambda x: x.created_at, reverse=True)

        # Compare each node with others in same namespace
        for i, node1 in enumerate(ns_nodes):
            # Skip if node is already in a group as a similar node
            if any(
                node1 in [s[0] for s in group.similar] for group in similarity_groups
            ):
                continue

            group = SimilarityGroup(node1)

            for node2 in ns_nodes[i + 1 :]:
                # Skip if node2 is already in a group
                if any(
                    node2 in [s[0] for s in group.similar]
                    for group in similarity_groups
                ):
                    continue

                # Calculate various similarity scores
                vector_sim = cosine_similarity(node1.embedding, node2.embedding)
                content_sim = content_similarity(node1.content, node2.content)
                tag_sim = tag_similarity(node1.tags or [], node2.tags or [])

                # Combine scores (weighted average)
                combined_sim = 0.5 * vector_sim + 0.3 * content_sim + 0.2 * tag_sim

                if combined_sim > CONTENT_SIMILARITY_THRESHOLD:
                    group.add_node(node2, combined_sim)

            if group.similar:  # Only add groups with similar nodes
                similarity_groups.append(group)

    return similarity_groups


async def process_similar_group(
    group: SimilarityGroup, dry_run: bool = False
) -> Dict[str, Any]:
    """
    Process a group of similar nodes. Either merge them or create edges.
    Returns stats about the operation.
    """
    stats = {"merged": 0, "linked": 0, "errors": 0}

    try:
        if group.should_merge():
            if not dry_run:
                async with MemorySessionLocal() as session:
                    # Merge metadata
                    all_tags = set(group.primary.tags or [])
                    all_categories = set(group.primary.categories or [])
                    merged_meta = json.loads(group.primary.meta or "{}")

                    # Collect metadata from similar nodes
                    for node, _ in group.similar:
                        if node.tags:
                            all_tags.update(node.tags)
                        if node.categories:
                            all_categories.update(node.categories)
                        node_meta = json.loads(node.meta or "{}")
                        merged_meta.update(node_meta)

                    # Update primary node
                    group.primary.tags = list(all_tags)
                    group.primary.categories = list(all_categories)
                    group.primary.meta = json.dumps(merged_meta)

                    # Add superseded_by references
                    for node, _ in group.similar:
                        node_meta = json.loads(node.meta or "{}")
                        node_meta["superseded_by"] = str(group.primary.id)
                        node.meta = json.dumps(node_meta)

                    session.add(group.primary)
                    for node, _ in group.similar:
                        session.add(node)
                    await session.commit()

            stats["merged"] = len(group.similar)

        else:
            # Create bidirectional edges between similar nodes
            if not dry_run:
                async with MemorySessionLocal() as session:
                    for node, similarity in group.similar:
                        edge1 = MemoryEdge(
                            from_id=group.primary.id,
                            to_id=node.id,
                            relation_type="similar_to",
                            meta=json.dumps(
                                {
                                    "similarity_score": similarity,
                                    "detection_method": "similarity_pruning_worker",
                                }
                            ),
                        )
                        edge2 = MemoryEdge(
                            from_id=node.id,
                            to_id=group.primary.id,
                            relation_type="similar_to",
                            meta=json.dumps(
                                {
                                    "similarity_score": similarity,
                                    "detection_method": "similarity_pruning_worker",
                                }
                            ),
                        )
                        session.add(edge1)
                        session.add(edge2)
                    await session.commit()

            stats["linked"] = len(group.similar) * 2  # Bidirectional edges

    except Exception as e:
        logger.error(f"Error processing similarity group: {e}")
        stats["errors"] = len(group.similar)

    return stats


async def process_similarity_pruning_job(job_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a similarity pruning job with the following config options:
    - scope: "all", "new", or "namespace:xyz"
    - dry_run: if true, only report changes
    - vector_similarity_threshold: float 0-1
    - content_similarity_threshold: float 0-1
    - tag_overlap_threshold: float 0-1
    """
    logger.critical("=== MEMORY SIMILARITY JOB STARTED (CRITICAL) ===")
    print("=== MEMORY SIMILARITY JOB STARTED (print) ===")
    stats = {
        "total_nodes": 0,
        "similar_groups": 0,
        "merged_nodes": 0,
        "linked_nodes": 0,
        "errors": 0,
        "start_time": time.time(),
    }

    try:
        # Update thresholds if provided
        global VECTOR_SIMILARITY_THRESHOLD, CONTENT_SIMILARITY_THRESHOLD, TAG_OVERLAP_THRESHOLD
        VECTOR_SIMILARITY_THRESHOLD = job_config.get(
            "vector_similarity_threshold", VECTOR_SIMILARITY_THRESHOLD
        )
        CONTENT_SIMILARITY_THRESHOLD = job_config.get(
            "content_similarity_threshold", CONTENT_SIMILARITY_THRESHOLD
        )
        TAG_OVERLAP_THRESHOLD = job_config.get(
            "tag_overlap_threshold", TAG_OVERLAP_THRESHOLD
        )

        # Get nodes based on scope
        async with MemorySessionLocal() as session:
            query = session.query(MemoryVector)
            if job_config.get("scope") == "new":
                # Only check nodes without any similarity edges
                subquery = (
                    session.query(MemoryEdge.from_id)
                    .filter(MemoryEdge.relation_type == "similar_to")
                    .distinct()
                )
                query = query.filter(~MemoryVector.id.in_(subquery))
            elif job_config.get("scope", "").startswith("namespace:"):
                namespace = job_config["scope"].split(":", 1)[1]
                query = query.filter(MemoryVector.namespace == namespace)
            nodes = await query.all()

        if not nodes:
            return {"status": "success", "message": "No nodes to process"}

        stats["total_nodes"] = len(nodes)

        # Process in batches
        for i in range(0, len(nodes), BATCH_SIZE):
            batch = nodes[i : i + BATCH_SIZE]

            # Find similar groups
            similarity_groups = await find_similar_nodes(batch)
            stats["similar_groups"] += len(similarity_groups)

            # Process each group
            for group in similarity_groups:
                group_stats = await process_similar_group(
                    group, dry_run=job_config.get("dry_run", False)
                )
                stats["merged_nodes"] += group_stats["merged"]
                stats["linked_nodes"] += group_stats["linked"]
                stats["errors"] += group_stats["errors"]

            # Log progress
            progress = (i + len(batch)) / len(nodes) * 100
            logger.info(
                f"Progress: {progress:.1f}% "
                f"({i + len(batch)}/{len(nodes)} nodes, "
                f"{stats['similar_groups']} groups found)"
            )

    except Exception as e:
        logger.error(f"Job processing error: {e}")
        return {"status": "error", "error": str(e), "stats": stats}

    stats["duration"] = time.time() - stats["start_time"]
    return {"status": "success", "stats": stats}


# For manual testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Memory similarity pruning worker")
    parser.add_argument("--dry-run", action="store_true", help="Don't apply changes")
    parser.add_argument("--scope", default="all", help="Scope of nodes to process")
    args = parser.parse_args()

    job = {"scope": args.scope, "dry_run": args.dry_run}
    asyncio.run(process_similarity_pruning_job(job))

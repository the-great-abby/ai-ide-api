import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import time
from sqlalchemy.exc import SQLAlchemyError
from db import MemorySessionLocal, MemoryVector
from memory import call_ollama_llm
import requests
import re

logger = logging.getLogger("memory_enrichment_worker")
logging.basicConfig(level=logging.INFO)

# Constants
DEFAULT_BATCH_SIZE = 50  # Default number of nodes per batch
MAX_BATCH_SIZE = 100  # Maximum nodes in a batch
MIN_BATCH_SIZE = 10  # Minimum nodes in a batch
TARGET_BATCH_TOKENS = 12000  # Target total tokens per batch

# Ollama endpoints
OLLAMA_URL = "http://host.docker.internal:11434"
OLLAMA_TOKENIZE_URL = f"{OLLAMA_URL}/api/tokenize"

# Retry settings
MAX_RETRIES = 3  # Max retries for LLM calls
RETRY_DELAY = 1  # Seconds between retries

# Example job payload:
# {
#   "scope": "all",           # or "new", "namespace:xyz", etc.
#   "dry_run": false,         # if true, only report changes
#   "similarity_threshold": 0.85,
#   "max_tags": 5,
#   "batch_size": 50,        # override default batch size
#   "target_batch_tokens": 12000  # override target tokens per batch
# }


def get_token_count(text: str) -> int:
    """Get accurate token count using Ollama's tokenizer."""
    try:
        response = requests.post(OLLAMA_TOKENIZE_URL, json={"content": text}, timeout=5)
        response.raise_for_status()
        tokens = response.json().get("tokens", [])
        return len(tokens)
    except Exception as e:
        logger.warning(f"Failed to get accurate token count, using estimate: {e}")
        # Fallback to rough estimation
        return int(len(text.split()) * 1.3)  # Rough estimate: words * 1.3


def calculate_dynamic_batch_size(nodes: List[MemoryVector]) -> List[List[MemoryVector]]:
    """Create batches based on token counts and system performance."""
    if not nodes:
        return []

    # Sort nodes by content length for better balancing
    nodes = sorted(nodes, key=lambda x: len(x.content))

    batches = []
    current_batch = []
    current_tokens = 0

    for node in nodes:
        # Get token count for this node
        node_tokens = get_token_count(node.content)

        # If this single node exceeds target, make it its own batch
        if node_tokens > TARGET_BATCH_TOKENS:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0
            batches.append([node])
            continue

        # If adding this node would exceed target, start new batch
        if current_tokens + node_tokens > TARGET_BATCH_TOKENS:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

        # Add node to current batch
        current_batch.append(node)
        current_tokens += node_tokens

        # If batch hits size limits, close it
        if len(current_batch) >= MAX_BATCH_SIZE:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

    # Add any remaining nodes
    if current_batch:
        batches.append(current_batch)

    return batches


class EnrichmentError(Exception):
    """Custom exception for enrichment-specific errors."""

    pass


async def retry_with_backoff(func, *args, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Retry a function with exponential backoff."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return await func(*args)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = delay * (2**attempt)  # Exponential backoff
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {wait}s..."
                )
                await asyncio.sleep(wait)
    raise EnrichmentError(
        f"Failed after {max_retries} attempts. Last error: {last_error}"
    )


async def extract_tags_llm(content: str, max_tags: int = 5) -> List[str]:
    """Extract tags using LLM with retry logic."""
    prompt = (
        f"Extract up to {max_tags} concise, relevant tags (single words or short phrases) "
        "that best describe the following text. Return as a comma-separated list.\n\n"
        f"Text:\n{content}\n\nTags:"
    )
    try:
        response = await retry_with_backoff(lambda: call_ollama_llm(prompt))
        tags = [t.strip() for t in response.split(",") if t.strip()]
        return tags[:max_tags]
    except EnrichmentError as e:
        logger.warning(f"LLM tag extraction failed after retries: {e}")
        return []


async def extract_categories_llm(content: str, max_tags: int = 5) -> List[str]:
    """Extract categories using LLM with retry logic."""
    prompt = (
        f"Extract up to {max_tags} high-level categories (single words or short phrases) "
        "that best classify the following text. Return as a comma-separated list.\n\n"
        f"Text:\n{content}\n\nCategories:"
    )
    try:
        response = await retry_with_backoff(lambda: call_ollama_llm(prompt))
        cats = [c.strip() for c in response.split(",") if c.strip()]
        return cats[:max_tags]
    except EnrichmentError as e:
        logger.warning(f"LLM category extraction failed after retries: {e}")
        return []


def extract_keywords(content: str, max_tags: int = 5) -> List[str]:
    """Extract keywords as fallback method."""
    try:
        words = re.findall(r"\b\w+\b", content.lower())
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq, key=freq.get, reverse=True)
        return sorted_words[:max_tags]
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        return []


async def process_node_batch(
    nodes: List[MemoryVector], max_tags: int
) -> List[Dict[str, Any]]:
    """Process a batch of nodes concurrently."""
    results = []
    for node in nodes:
        try:
            # Run tag and category extraction concurrently
            tags_task = extract_tags_llm(node.content, max_tags)
            cats_task = extract_categories_llm(node.content, max_tags)
            tags, categories = await asyncio.gather(tags_task, cats_task)

            # Fallback to keyword extraction if needed
            if not tags:
                tags = extract_keywords(node.content, max_tags)
            if not categories:
                categories = extract_keywords(node.content, max_tags)

            # Deduplicate and limit
            tags = list(dict.fromkeys(tags))[:max_tags]
            categories = list(dict.fromkeys(categories))[:max_tags]

            results.append(
                {
                    "node": node,
                    "tags": tags,
                    "categories": categories,
                    "success": True,
                    "error": None,
                }
            )
        except Exception as e:
            logger.error(f"Failed to process node {node.id}: {e}")
            results.append(
                {
                    "node": node,
                    "tags": [],
                    "categories": [],
                    "success": False,
                    "error": str(e),
                }
            )
    return results


async def process_batch(
    batch: List[MemoryVector], job_config: Dict[str, Any]
) -> Tuple[int, int]:
    """Process a batch of nodes, returning (success_count, error_count)."""
    success_count = 0
    error_count = 0

    try:
        # Group similar nodes
        similar_groups = await find_similar_nodes(batch)

        # Extract tags and categories
        for group in similar_groups:
            try:
                tags, categories = await extract_tags_and_categories(group)

                if not job_config.get("dry_run", False):
                    # Update nodes with new tags and categories
                    async with MemorySessionLocal() as session:
                        for node in group:
                            node.tags = tags
                            node.categories = categories
                            session.add(node)
                        await session.commit()

                success_count += len(group)
            except Exception as e:
                logger.error(f"Error processing group: {e}")
                error_count += len(group)

    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        error_count += len(batch)

    return success_count, error_count


async def process_enrichment_job(job_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an enrichment job with the following config options:
    - scope: "all", "new", or "namespace:xyz"
    - dry_run: if true, only report changes
    - similarity_threshold: float 0-1
    - max_tags: int
    - batch_size: int (optional)
    """
    stats = {"processed": 0, "errors": 0, "batches": 0, "start_time": time.time()}

    try:
        # Get nodes based on scope
        async with MemorySessionLocal() as session:
            query = session.query(MemoryVector)
            if job_config.get("scope") == "new":
                query = query.filter(MemoryVector.tags == None)
            elif job_config.get("scope", "").startswith("namespace:"):
                namespace = job_config["scope"].split(":", 1)[1]
                query = query.filter(MemoryVector.namespace == namespace)
            nodes = await query.all()

        if not nodes:
            return {"status": "success", "message": "No nodes to process"}

        # Create dynamic batches
        batches = calculate_dynamic_batch_size(nodes)
        stats["total_nodes"] = len(nodes)
        stats["total_batches"] = len(batches)

        # Process batches
        for i, batch in enumerate(batches):
            success, errors = await process_batch(batch, job_config)
            stats["processed"] += success
            stats["errors"] += errors
            stats["batches"] += 1

            # Log progress
            progress = (i + 1) / len(batches) * 100
            logger.info(f"Progress: {progress:.1f}% ({i + 1}/{len(batches)} batches)")

    except Exception as e:
        logger.error(f"Job processing error: {e}")
        return {"status": "error", "error": str(e), "stats": stats}

    stats["duration"] = time.time() - stats["start_time"]
    return {"status": "success", "stats": stats}


# TODO: Implement these core functions
async def find_similar_nodes(nodes: List[MemoryVector]) -> List[List[MemoryVector]]:
    """Group similar nodes together."""
    # TODO: Implement similarity detection
    return [nodes]  # For now, return all nodes as one group


async def extract_tags_and_categories(
    nodes: List[MemoryVector],
) -> Tuple[List[str], List[str]]:
    """Extract tags and categories for a group of similar nodes."""
    # TODO: Implement tag and category extraction
    return [], []  # For now, return empty lists


# For manual testing
if __name__ == "__main__":
    import sys
    import json

    # Example: python scripts/memory_enrichment_worker.py '{"scope": "all", "dry_run": true}'
    if len(sys.argv) > 1:
        job = json.loads(sys.argv[1])
    else:
        job = {"scope": "all", "dry_run": True}
    asyncio.run(process_enrichment_job(job))

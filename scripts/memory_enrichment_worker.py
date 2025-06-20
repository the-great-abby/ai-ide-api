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
            logger.info(f"[ENRICHMENT] 🔄 LLM attempt {attempt + 1}/{max_retries}")
            return await func(*args)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = delay * (2**attempt)  # Exponential backoff
                logger.warning(
                    f"[ENRICHMENT] ⚠️ LLM attempt {attempt + 1} failed: {e}. Retrying in {wait}s..."
                )
                await asyncio.sleep(wait)
            else:
                logger.error(f"[ENRICHMENT] ❌ LLM failed after {max_retries} attempts. Last error: {last_error}")
    raise EnrichmentError(
        f"Failed after {max_retries} attempts. Last error: {last_error}"
    )


def clean_llm_list_output(text: str) -> list[str]:
    """Extract only the actual tags/categories from LLM output, removing boilerplate."""
    # Split into lines, ignore lines that look like instructions
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # Remove lines that are instructions or explanations
    filtered = []
    for line in lines:
        # Skip lines that look like instructions
        if re.search(r"here (are|is) (the|a|up to)? ?(extracted|relevant|top|high-level)? ?(tags|categories|list|comma-separated|that|best|describe|classify|as|in|to|of|for|with|by|\d+|:|,|\.|\n)*", line, re.IGNORECASE):
            continue
        filtered.append(line)
    # If nothing left, fallback to all lines
    if not filtered:
        filtered = lines
    # Join and split by comma
    joined = ", ".join(filtered)
    items = [t.strip() for t in joined.split(",") if t.strip()]
    return items


async def extract_tags_llm(content: str, max_tags: int = 5) -> list[str]:
    logger.info(f"[ENRICHMENT] 🏷️ Extracting tags from content (max: {max_tags})")
    prompt = (
        f"Extract up to {max_tags} relevant tags (single words or short phrases) "
        "that best describe the following text. Return as a comma-separated list.\n\n"
        f"Text:\n{content}\n\nTags:"
    )
    logger.info(f"[ENRICHMENT] [PROMPT] LLM prompt for tags:\n{prompt}")
    try:
        logger.info("[ENRICHMENT] 🤖 Calling LLM for tag extraction...")
        async def call_llm():
            return await asyncio.to_thread(call_ollama_llm, prompt)
        response = await retry_with_backoff(call_llm)
        tags = clean_llm_list_output(response)
        tags = tags[:max_tags]
        logger.info(f"[ENRICHMENT] ✅ LLM extracted tags: {tags}")
        return tags
    except EnrichmentError as e:
        logger.warning(f"[ENRICHMENT] ⚠️ LLM tag extraction failed after retries: {e}")
        return []


async def extract_categories_llm(content: str, max_tags: int = 5) -> list[str]:
    logger.info(f"[ENRICHMENT] 📂 Extracting categories from content (max: {max_tags})")
    prompt = (
        f"Extract up to {max_tags} high-level categories (single words or short phrases) "
        "that best classify the following text. Return as a comma-separated list.\n\n"
        f"Text:\n{content}\n\nCategories:"
    )
    logger.info(f"[ENRICHMENT] [PROMPT] LLM prompt for categories:\n{prompt}")
    try:
        logger.info("[ENRICHMENT] 🤖 Calling LLM for category extraction...")
        async def call_llm():
            return await asyncio.to_thread(call_ollama_llm, prompt)
        response = await retry_with_backoff(call_llm)
        cats = clean_llm_list_output(response)
        cats = cats[:max_tags]
        logger.info(f"[ENRICHMENT] ✅ LLM extracted categories: {cats}")
        return cats
    except EnrichmentError as e:
        logger.warning(f"[ENRICHMENT] ⚠️ LLM category extraction failed after retries: {e}")
        return []


def extract_keywords(content: str, max_tags: int = 5) -> List[str]:
    """Extract keywords as fallback method."""
    logger.info(f"[ENRICHMENT] 🔤 Extracting keywords as fallback (max: {max_tags})")
    try:
        words = re.findall(r"\b\w+\b", content.lower())
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq, key=freq.get, reverse=True)
        keywords = sorted_words[:max_tags]
        logger.info(f"[ENRICHMENT] ✅ Keyword extraction result: {keywords}")
        return keywords
    except Exception as e:
        logger.error(f"[ENRICHMENT] ❌ Keyword extraction failed: {e}")
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


async def process_enrichment_job(job_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an enrichment job with the following config options:
    - scope: "all", "new", or "namespace:xyz"
    - dry_run: if true, only report changes
    - similarity_threshold: float 0-1
    - max_tags: int
    - batch_size: int (optional)
    """
    print("=== ENRICHMENT JOB STARTED ===")
    logger.critical("=== ENRICHMENT JOB STARTED (CRITICAL) ===")
    logger.error("=== ENRICHMENT JOB STARTED (ERROR) ===")
    logger.warning("=== ENRICHMENT JOB STARTED (WARNING) ===")
    logger.info(f"[ENRICHMENT] 🚀 Starting enrichment job with config: {job_config}")
    stats = {"processed": 0, "errors": 0, "batches": 0, "start_time": time.time()}

    try:
        # Get nodes based on scope
        logger.info(f"[ENRICHMENT] 📊 Querying nodes with scope: {job_config.get('scope', 'all')}")
        session = MemorySessionLocal()
        try:
            query = session.query(MemoryVector)
            
            # Apply scope filter
            scope = job_config.get('scope', 'all')
            if scope == 'new':
                # Only process nodes without tags/categories
                query = query.filter(
                    (MemoryVector.tags == None) | (MemoryVector.tags == []) |
                    (MemoryVector.categories == None) | (MemoryVector.categories == [])
                )
            elif scope.startswith('namespace:'):
                namespace = scope.split(':', 1)[1]
                query = query.filter(MemoryVector.namespace == namespace)
            
            # Get total count for progress tracking
            total_count = query.count()
            logger.info(f"[ENRICHMENT] 📈 Found {total_count} memories to process")
            
            if total_count == 0:
                logger.info("[ENRICHMENT] ✅ No memories to process, job complete")
                return {"status": "success", "message": "No memories to process", **stats}
            
            # Process in batches
            batch_size = job_config.get('batch_size', 10)
            offset = 0
            
            while offset < total_count:
                logger.info(f"[ENRICHMENT] 🔄 Processing batch {stats['batches'] + 1} (offset: {offset}, batch_size: {batch_size})")
                
                # Get batch of memories
                batch_query = query.offset(offset).limit(batch_size)
                memories = batch_query.all()
                
                if not memories:
                    logger.warning(f"[ENRICHMENT] ⚠️ No memories found in batch at offset {offset}")
                    break
                
                logger.info(f"[ENRICHMENT] 📝 Processing {len(memories)} memories in this batch")
                
                # Process each memory in the batch
                for memory in memories:
                    try:
                        logger.info(f"[ENRICHMENT] 🧠 Processing memory ID: {memory.id}")
                        
                        # Extract tags and categories using LLM
                        if memory.content:
                            logger.info(f"[ENRICHMENT] 🤖 Extracting tags for memory {memory.id}")
                            tags = await extract_tags_llm(memory.content, job_config.get('max_tags', 5))
                            logger.info(f"[ENRICHMENT] [DEBUG] Tags extracted for {memory.id}: {tags}")
                            
                            logger.info(f"[ENRICHMENT] 🤖 Extracting categories for memory {memory.id}")
                            categories = await extract_categories_llm(memory.content)
                            logger.info(f"[ENRICHMENT] [DEBUG] Categories extracted for {memory.id}: {categories}")
                            
                            logger.info(f"[ENRICHMENT] 📊 Memory {memory.id} - Tags: {tags}, Categories: {categories}")
                            
                            # Update memory if not dry run
                            if not job_config.get('dry_run', False):
                                logger.info(f"[ENRICHMENT] [DEBUG] About to update DB for {memory.id}")
                                memory.tags = tags
                                memory.categories = categories
                                logger.info(f"[ENRICHMENT] 💾 Updated memory {memory.id} in database (pre-commit)")
                            else:
                                logger.info(f"[ENRICHMENT] 🔍 DRY RUN - Would update memory {memory.id} with tags: {tags}, categories: {categories}")
                            
                            stats['processed'] += 1
                        else:
                            logger.warning(f"[ENRICHMENT] ⚠️ Memory {memory.id} has no content, skipping")
                            
                    except Exception as e:
                        logger.error(f"[ENRICHMENT] ❌ Error processing memory {memory.id}: {e}")
                        stats['errors'] += 1
                
                # Commit batch if not dry run
                if not job_config.get('dry_run', False):
                    logger.info(f"[ENRICHMENT] [DEBUG] About to commit batch {stats['batches'] + 1}")
                    session.commit()
                    logger.info(f"[ENRICHMENT] ✅ Committed batch {stats['batches'] + 1}")
                else:
                    logger.info(f"[ENRICHMENT] 🔍 DRY RUN - Would commit batch {stats['batches'] + 1}")
                
                stats['batches'] += 1
                offset += batch_size
                
                # Small delay between batches to be nice to the system
                await asyncio.sleep(0.1)
            
            # Final stats
            duration = time.time() - stats['start_time']
            logger.info(f"[ENRICHMENT] 🎉 Enrichment job completed! Processed: {stats['processed']}, Errors: {stats['errors']}, Batches: {stats['batches']}, Duration: {duration:.2f}s")
            
            return {
                "status": "success",
                "processed": stats['processed'],
                "errors": stats['errors'],
                "batches": stats['batches'],
                "duration": duration
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"[ENRICHMENT] 💥 Fatal error in enrichment job: {e}")
        return {
            "status": "error",
            "error": str(e),
            **stats
        }


async def find_similar_nodes(nodes: List[MemoryVector]) -> List[List[MemoryVector]]:
    """Group similar nodes together based on content similarity."""
    logger.info(f"[ENRICHMENT] 🔍 Finding similar nodes among {len(nodes)} nodes")
    
    if len(nodes) <= 1:
        return [nodes]
    
    # For now, group by namespace as a simple similarity metric
    # TODO: Implement more sophisticated similarity detection using embeddings
    groups = {}
    for node in nodes:
        namespace = node.namespace or "default"
        if namespace not in groups:
            groups[namespace] = []
        groups[namespace].append(node)
    
    result = list(groups.values())
    logger.info(f"[ENRICHMENT] 📊 Grouped nodes into {len(result)} similarity groups")
    return result


async def extract_tags_and_categories(
    nodes: List[MemoryVector],
) -> Tuple[List[str], List[str]]:
    """Extract tags and categories for a group of similar nodes."""
    logger.info(f"[ENRICHMENT] 🏷️ Extracting tags and categories for {len(nodes)} nodes")
    
    if not nodes:
        return [], []
    
    # Use the first node's content as representative for the group
    # TODO: Implement more sophisticated group analysis
    representative_content = nodes[0].content
    max_tags = 5  # Default value, could be configurable
    
    try:
        # Extract tags and categories concurrently
        tags_task = extract_tags_llm(representative_content, max_tags)
        categories_task = extract_categories_llm(representative_content, max_tags)
        
        tags, categories = await asyncio.gather(tags_task, categories_task)
        
        # Fallback to keyword extraction if LLM fails
        if not tags:
            logger.info("[ENRICHMENT] 🔄 LLM tag extraction failed, using keyword fallback")
            tags = extract_keywords(representative_content, max_tags)
        if not categories:
            logger.info("[ENRICHMENT] 🔄 LLM category extraction failed, using keyword fallback")
            categories = extract_keywords(representative_content, max_tags)
        
        # Deduplicate and limit
        tags = list(dict.fromkeys(tags))[:max_tags]
        categories = list(dict.fromkeys(categories))[:max_tags]
        
        logger.info(f"[ENRICHMENT] ✅ Extracted tags: {tags}, categories: {categories}")
        return tags, categories
        
    except Exception as e:
        logger.error(f"[ENRICHMENT] ❌ Failed to extract tags/categories: {e}")
        return [], []


async def process_batch(
    batch: List[MemoryVector], job_config: Dict[str, Any]
) -> Tuple[int, int]:
    """Process a batch of nodes, returning (success_count, error_count)."""
    logger.info(f"[ENRICHMENT] 🔄 Processing batch of {len(batch)} nodes")
    success_count = 0
    error_count = 0

    try:
        # Group similar nodes
        similar_groups = await find_similar_nodes(batch)
        logger.info(f"[ENRICHMENT] 📊 Processing {len(similar_groups)} similarity groups")

        # Extract tags and categories for each group
        for i, group in enumerate(similar_groups):
            try:
                logger.info(f"[ENRICHMENT] 🏷️ Processing group {i + 1}/{len(similar_groups)} ({len(group)} nodes)")
                tags, categories = await extract_tags_and_categories(group)

                if not job_config.get("dry_run", False):
                    # Update nodes with new tags and categories
                    logger.info(f"[ENRICHMENT] 💾 Updating {len(group)} nodes with tags: {tags}, categories: {categories}")
                    session = MemorySessionLocal()
                    try:
                        for node in group:
                            node.tags = tags
                            node.categories = categories
                            session.add(node)
                        session.commit()
                        logger.info(f"[ENRICHMENT] ✅ Successfully updated {len(group)} nodes in database")
                    finally:
                        session.close()
                else:
                    logger.info(f"[ENRICHMENT] 🔍 DRY RUN: Would update {len(group)} nodes with tags: {tags}, categories: {categories}")

                success_count += len(group)
            except Exception as e:
                logger.error(f"[ENRICHMENT] ❌ Error processing group {i + 1}: {e}")
                error_count += len(group)

    except Exception as e:
        logger.error(f"[ENRICHMENT] ❌ Batch processing error: {e}")
        error_count += len(batch)

    logger.info(f"[ENRICHMENT] 📊 Batch complete - Success: {success_count}, Errors: {error_count}")
    return success_count, error_count


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

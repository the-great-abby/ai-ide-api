import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import time
from sqlalchemy.exc import SQLAlchemyError
from db import MemorySessionLocal, MemoryVector, MemoryEdge
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

# Edge creation constants
TAG_SIMILARITY_THRESHOLD = 0.3  # Minimum ratio of shared tags to create edge
CONTENT_REFERENCE_PATTERN = r'[a-f0-9]{8,}'  # Pattern to match potential node IDs
MAX_EDGES_PER_NODE = 20  # Maximum edges to create per node to avoid spam

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
#   "target_batch_tokens": 12000,  # override target tokens per batch
#   "create_edges": true,    # whether to create edges after enrichment
#   "edge_types": ["tag_based", "content_ref"]  # types of edges to create
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


async def create_tag_based_edges(
    enriched_nodes: List[MemoryVector], 
    dry_run: bool = False
) -> Dict[str, int]:
    """Create edges between nodes that share tags."""
    logger.info(f"[ENRICHMENT] 🔗 Creating tag-based edges for {len(enriched_nodes)} nodes")
    stats = {"created": 0, "skipped": 0, "errors": 0}
    
    try:
        # Group nodes by their tags
        tag_groups = {}
        for node in enriched_nodes:
            if node.tags:
                for tag in node.tags:
                    if tag not in tag_groups:
                        tag_groups[tag] = []
                    tag_groups[tag].append(node)
        
        # Create edges for nodes sharing tags
        created_edges = set()  # Track (from_id, to_id) pairs to avoid duplicates
        
        for tag, nodes in tag_groups.items():
            if len(nodes) < 2:
                continue
                
            # Create edges between all pairs of nodes with this tag
            for i, node1 in enumerate(nodes):
                edges_created = 0
                for node2 in nodes[i+1:]:
                    # Avoid self-loops and duplicate edges
                    edge_key = tuple(sorted([str(node1.id), str(node2.id)]))
                    if edge_key in created_edges:
                        continue
                    
                    # Calculate tag similarity ratio
                    shared_tags = set(node1.tags or []) & set(node2.tags or [])
                    total_tags = set(node1.tags or []) | set(node2.tags or [])
                    similarity_ratio = len(shared_tags) / len(total_tags) if total_tags else 0
                    
                    if similarity_ratio >= TAG_SIMILARITY_THRESHOLD:
                        if not dry_run:
                            try:
                                session = MemorySessionLocal()
                                edge = MemoryEdge(
                                    from_id=str(node1.id),
                                    to_id=str(node2.id),
                                    relation_type="shared_tag",
                                    meta=json.dumps({
                                        "shared_tags": list(shared_tags),
                                        "similarity_ratio": similarity_ratio,
                                        "created_by": "memory_enrichment_worker"
                                    })
                                )
                                session.add(edge)
                                session.commit()
                                session.close()
                                
                                logger.info(f"[ENRICHMENT] 🔗 Created edge {node1.id} → {node2.id} (shared tags: {list(shared_tags)})")
                                stats["created"] += 1
                                created_edges.add(edge_key)
                                edges_created += 1
                                
                                # Limit edges per node to avoid spam
                                if edges_created >= MAX_EDGES_PER_NODE:
                                    break
                                    
                            except Exception as e:
                                logger.error(f"[ENRICHMENT] ❌ Error creating edge {node1.id} → {node2.id}: {e}")
                                stats["errors"] += 1
                        else:
                            logger.info(f"[ENRICHMENT] 🔍 DRY RUN - Would create edge {node1.id} → {node2.id} (shared tags: {list(shared_tags)})")
                            stats["created"] += 1
                    else:
                        stats["skipped"] += 1
        
        logger.info(f"[ENRICHMENT] ✅ Tag-based edge creation complete: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"[ENRICHMENT] ❌ Error in tag-based edge creation: {e}")
        stats["errors"] += 1
        return stats


async def create_content_reference_edges(
    enriched_nodes: List[MemoryVector], 
    all_nodes: List[MemoryVector],
    dry_run: bool = False
) -> Dict[str, int]:
    """Create edges when one node's content references another node's ID."""
    logger.info(f"[ENRICHMENT] 🔗 Creating content reference edges for {len(enriched_nodes)} nodes")
    stats = {"created": 0, "skipped": 0, "errors": 0}
    
    try:
        # Create lookup of all node IDs
        node_ids = {str(node.id) for node in all_nodes}
        created_edges = set()
        
        for node in enriched_nodes:
            if not node.content:
                continue
                
            # Find potential node ID references in content
            potential_refs = re.findall(CONTENT_REFERENCE_PATTERN, node.content)
            edges_created = 0
            
            for ref in potential_refs:
                # Check if this reference matches an actual node ID
                if ref in node_ids and ref != str(node.id):
                    edge_key = tuple(sorted([str(node.id), ref]))
                    if edge_key in created_edges:
                        continue
                        
                    if not dry_run:
                        try:
                            session = MemorySessionLocal()
                            edge = MemoryEdge(
                                from_id=str(node.id),
                                to_id=ref,
                                relation_type="content_ref",
                                meta=json.dumps({
                                    "reference_type": "id_mention",
                                    "matched_pattern": ref,
                                    "created_by": "memory_enrichment_worker"
                                })
                            )
                            session.add(edge)
                            session.commit()
                            session.close()
                            
                            logger.info(f"[ENRICHMENT] 🔗 Created content ref edge {node.id} → {ref}")
                            stats["created"] += 1
                            created_edges.add(edge_key)
                            edges_created += 1
                            
                            if edges_created >= MAX_EDGES_PER_NODE:
                                break
                                
                        except Exception as e:
                            logger.error(f"[ENRICHMENT] ❌ Error creating content ref edge {node.id} → {ref}: {e}")
                            stats["errors"] += 1
                    else:
                        logger.info(f"[ENRICHMENT] 🔍 DRY RUN - Would create content ref edge {node.id} → {ref}")
                        stats["created"] += 1
                else:
                    stats["skipped"] += 1
        
        logger.info(f"[ENRICHMENT] ✅ Content reference edge creation complete: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"[ENRICHMENT] ❌ Error in content reference edge creation: {e}")
        stats["errors"] += 1
        return stats


async def create_edges_after_enrichment(
    enriched_nodes: List[MemoryVector],
    all_nodes: List[MemoryVector],
    job_config: Dict[str, Any]
) -> Dict[str, int]:
    """Create edges after enrichment based on job configuration."""
    logger.info(f"[ENRICHMENT] 🔗 Starting edge creation phase")
    
    if not job_config.get("create_edges", False):
        logger.info("[ENRICHMENT] ⏭️ Edge creation disabled in job config")
        return {"created": 0, "skipped": 0, "errors": 0}
    
    edge_types = job_config.get("edge_types", ["tag_based", "content_ref"])
    total_stats = {"created": 0, "skipped": 0, "errors": 0}
    dry_run = job_config.get("dry_run", False)
    
    try:
        # Create tag-based edges
        if "tag_based" in edge_types:
            logger.info("[ENRICHMENT] 🔗 Creating tag-based edges...")
            tag_stats = await create_tag_based_edges(enriched_nodes, dry_run)
            for key in total_stats:
                total_stats[key] += tag_stats.get(key, 0)
        
        # Create content reference edges
        if "content_ref" in edge_types:
            logger.info("[ENRICHMENT] 🔗 Creating content reference edges...")
            content_stats = await create_content_reference_edges(enriched_nodes, all_nodes, dry_run)
            for key in total_stats:
                total_stats[key] += content_stats.get(key, 0)
        
        logger.info(f"[ENRICHMENT] 🎉 Edge creation phase complete: {total_stats}")
        return total_stats
        
    except Exception as e:
        logger.error(f"[ENRICHMENT] ❌ Error in edge creation phase: {e}")
        total_stats["errors"] += 1
        return total_stats


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
    - create_edges: bool (whether to create edges after enrichment)
    - edge_types: list of edge types to create
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
            
            # Get all nodes for edge creation (if enabled)
            all_nodes = []
            if job_config.get("create_edges", False):
                logger.info("[ENRICHMENT] 📋 Fetching all nodes for edge creation...")
                all_nodes = session.query(MemoryVector).all()
                logger.info(f"[ENRICHMENT] 📋 Found {len(all_nodes)} total nodes for edge creation")
            
            # Process in batches
            batch_size = job_config.get('batch_size', 10)
            offset = 0
            enriched_nodes = []  # Track enriched nodes for edge creation
            
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
                            
                            # Track enriched nodes for edge creation
                            enriched_nodes.append(memory)
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
            
            # Edge creation phase
            edge_stats = {"edges_created": 0, "edges_skipped": 0, "edge_errors": 0}
            if job_config.get("create_edges", False) and enriched_nodes:
                logger.info(f"[ENRICHMENT] 🔗 Starting edge creation phase for {len(enriched_nodes)} enriched nodes")
                edge_stats = await create_edges_after_enrichment(enriched_nodes, all_nodes, job_config)
                stats.update(edge_stats)
            
            # Final stats
            duration = time.time() - stats['start_time']
            logger.info(f"[ENRICHMENT] 🎉 Enrichment job completed! Processed: {stats['processed']}, Errors: {stats['errors']}, Batches: {stats['batches']}, Edges Created: {stats.get('edges_created', 0)}, Duration: {duration:.2f}s")
            
            return {
                "status": "success",
                "processed": stats['processed'],
                "errors": stats['errors'],
                "batches": stats['batches'],
                "edges_created": stats.get('edges_created', 0),
                "edges_skipped": stats.get('edges_skipped', 0),
                "edge_errors": stats.get('edge_errors', 0),
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

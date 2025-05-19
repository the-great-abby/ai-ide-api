"""
Memory Edge Inference Module

Provides functions to extract and infer edges (relationships) between memory nodes based on:
- Explicit relationships (from API)
- Shared tags/metadata
- Content references
- (Future) Custom user-defined rules
"""

from typing import List, Dict, Any
import json


def extract_explicit_edges(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Return the list of explicit edges as-is from the API/database.
    """
    return edges


def extract_tag_based_edges(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Infer edges between nodes that share tags or metadata.
    Returns a list of inferred edge dicts: {from_id, to_id, relation_type, meta}
    """
    inferred_edges = []
    # Parse tags for each node
    node_tags = {}
    for node in nodes:
        meta = node.get("meta", "{}")
        try:
            meta_dict = json.loads(meta)
            tags = set(meta_dict.get("tags", []))
        except Exception:
            tags = set()
        node_tags[node["id"]] = tags
    # For each pair of nodes, infer edge if they share at least one tag
    node_ids = list(node_tags.keys())
    for i, id1 in enumerate(node_ids):
        for id2 in node_ids:
            if id1 == id2:
                continue
            shared = node_tags[id1] & node_tags[id2]
            if shared:
                inferred_edges.append({
                    "from_id": id1,
                    "to_id": id2,
                    "relation_type": "shared_tag",
                    "meta": json.dumps({"shared_tags": list(shared)})
                })
    return inferred_edges


def extract_content_based_edges(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Infer edges between nodes based on content references (e.g., one node mentions another).
    Returns a list of inferred edge dicts: {from_id, to_id, relation_type, meta}
    """
    inferred_edges = []
    node_ids = {node["id"] for node in nodes}
    for node in nodes:
        from_id = node["id"]
        content = node.get("content", "")
        for to_id in node_ids:
            if from_id == to_id:
                continue
            if to_id in content:
                inferred_edges.append({
                    "from_id": from_id,
                    "to_id": to_id,
                    "relation_type": "content_ref",
                    "meta": f'{{"matched_id": "{to_id}"}}'
                })
    return inferred_edges


def extract_custom_edges(nodes: List[Dict[str, Any]], config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Apply user-defined/custom rules to infer edges.
    Returns a list of inferred edge dicts: {from_id, to_id, relation_type, meta}
    """
    # TODO: Implement custom rule-based edge inference
    return []


def main():
    """
    Entry point for CLI/script usage. (To be implemented)
    """
    pass


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
import os
import json
import requests
from typing import Optional, Dict, List, Any

# Use Docker service names when running in Docker, otherwise use localhost
API_URL = os.environ.get(
    "MEMORY_API_URL",
    "http://api:8000/memory/nodes" if os.environ.get("RUNNING_IN_DOCKER") else "http://localhost:9103/memory/nodes"
)

def add_node(namespace: str, content: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Add a new node to the memory graph."""
    payload = {
        "namespace": namespace,
        "content": content,
        "meta": meta or {}
    }
    response = requests.post(f"{API_URL}/nodes", json=payload)
    response.raise_for_status()
    return response.json()

def add_edge(from_id: str, to_id: str, relation_type: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Add a new edge to the memory graph."""
    payload = {
        "from_id": from_id,
        "to_id": to_id,
        "relation_type": relation_type,
        "meta": meta or {}
    }
    response = requests.post(f"{API_URL}/edges", json=payload)
    response.raise_for_status()
    return response.json()

def list_nodes() -> List[Dict[str, Any]]:
    """List all nodes in the memory graph."""
    response = requests.get(f"{API_URL}/nodes")
    response.raise_for_status()
    return response.json()

def list_edges() -> List[Dict[str, Any]]:
    """List all edges in the memory graph."""
    response = requests.get(f"{API_URL}/edges")
    response.raise_for_status()
    return response.json()

def traverse_single_hop(node_id: str) -> List[Dict[str, Any]]:
    """Traverse one level of relationships from a node."""
    response = requests.get(f"{API_URL}/nodes/{node_id}/traverse?hops=1")
    response.raise_for_status()
    return response.json()

def traverse_multi_hop(node_id: str, max_hops: int = 3) -> List[Dict[str, Any]]:
    """Traverse multiple levels of relationships from a node."""
    response = requests.get(f"{API_URL}/nodes/{node_id}/traverse?hops={max_hops}")
    response.raise_for_status()
    return response.json()

def traverse_by_relation(node_id: str, relation_type: str) -> List[Dict[str, Any]]:
    """Traverse relationships of a specific type from a node."""
    response = requests.get(f"{API_URL}/nodes/{node_id}/traverse?relation_type={relation_type}")
    response.raise_for_status()
    return response.json()

def export_dot() -> str:
    """Export the memory graph in DOT format."""
    edges = list_edges()
    dot = ["digraph MemoryGraph {"]
    for edge in edges:
        dot.append(f'    "{edge["from_id"]}" -> "{edge["to_id"]}" [label="{edge["relation_type"]}"];')
    dot.append("}")
    return "\n".join(dot)

def delete_nodes(namespace: Optional[str] = None) -> None:
    """Delete nodes from the memory graph, optionally filtered by namespace."""
    url = f"{API_URL}/nodes"
    if namespace:
        url += f"?namespace={namespace}"
    response = requests.delete(url)
    response.raise_for_status() 
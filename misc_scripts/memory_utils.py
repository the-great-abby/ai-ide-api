#!/usr/bin/env python3
import os
import json
import requests
from typing import Optional, Dict, List, Any

# Use Docker service names when running in Docker, otherwise use localhost
API_URL = os.environ.get(
    "MEMORY_API_URL",
    "http://api:8000/memory"
    if os.environ.get("RUNNING_IN_DOCKER")
    else "http://localhost:9104/memory",
)


def get_auth_header() -> dict:
    token = os.environ.get("APITOKEN")
    if not token:
        token_path = "/code/.apitoken"
        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                token = f.read().strip()
    if not token:
        raise RuntimeError("No API token found in APITOKEN env or /code/.apitoken")
    return {"Authorization": f"Bearer {token}"}


def add_memory_node(namespace: str, content: str, meta: Optional[Any] = None) -> Dict:
    url = f"{API_URL}/nodes"
    headers = get_auth_header()
    payload = {
        "namespace": namespace,
        "content": content,
    }
    if meta is not None:
        if isinstance(meta, dict):
            payload["meta"] = json.dumps(meta)
        elif isinstance(meta, str):
            payload["meta"] = meta
        else:
            raise ValueError("meta must be a dict, str, or None")
    else:
        payload["meta"] = None
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()


def add_edge(
    from_id: str, to_id: str, relation_type: str, meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Add a new edge to the memory graph."""
    payload = {
        "from_id": from_id,
        "to_id": to_id,
        "relation_type": relation_type,
        "meta": meta or {},
    }
    headers = get_auth_header()
    response = requests.post(f"{API_URL}/edges", json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def list_nodes() -> List[Dict[str, Any]]:
    """List all nodes in the memory graph."""
    headers = get_auth_header()
    response = requests.get(f"{API_URL}/nodes", headers=headers)
    response.raise_for_status()
    return response.json()


def list_edges() -> List[Dict[str, Any]]:
    """List all edges in the memory graph."""
    headers = get_auth_header()
    response = requests.get(f"{API_URL}/edges", headers=headers)
    response.raise_for_status()
    return response.json()


def traverse_single_hop(node_id: str) -> List[Dict[str, Any]]:
    """Traverse one level of relationships from a node."""
    headers = get_auth_header()
    response = requests.get(
        f"{API_URL}/nodes/{node_id}/traverse?hops=1", headers=headers
    )
    response.raise_for_status()
    return response.json()


def traverse_multi_hop(node_id: str, max_hops: int = 3) -> List[Dict[str, Any]]:
    """Traverse multiple levels of relationships from a node."""
    headers = get_auth_header()
    response = requests.get(
        f"{API_URL}/nodes/{node_id}/traverse?hops={max_hops}", headers=headers
    )
    response.raise_for_status()
    return response.json()


def traverse_by_relation(node_id: str, relation_type: str) -> List[Dict[str, Any]]:
    """Traverse relationships of a specific type from a node."""
    headers = get_auth_header()
    response = requests.get(
        f"{API_URL}/nodes/{node_id}/traverse?relation_type={relation_type}",
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


def export_dot() -> str:
    """Export the memory graph in DOT format."""
    edges = list_edges()
    dot = ["digraph MemoryGraph {"]
    for edge in edges:
        dot.append(
            f'    "{edge["from_id"]}" -> "{edge["to_id"]}" [label="{edge["relation_type"]}"];'
        )
    dot.append("}")
    return "\n".join(dot)


def delete_nodes(namespace: Optional[str] = None) -> None:
    """Delete nodes from the memory graph, optionally filtered by namespace."""
    url = f"{API_URL}/nodes"
    if namespace:
        url += f"?namespace={namespace}"
    headers = get_auth_header()
    response = requests.delete(url, headers=headers)
    response.raise_for_status()

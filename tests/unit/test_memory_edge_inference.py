import pytest
pytestmark = pytest.mark.unit
from scripts.memory_edge_inference import (
    extract_explicit_edges,
    extract_tag_based_edges,
    extract_content_based_edges,
    extract_custom_edges,
)


def test_extract_explicit_edges(memory_node):
    nodes = [
        memory_node("A", node_id="n1"),
        memory_node("B", node_id="n2"),
    ]
    edges = [
        {"from_id": "n1", "to_id": "n2", "relation_type": "test", "meta": "{}"}
    ]
    result = extract_explicit_edges(nodes, edges)
    assert result == edges


def test_extract_tag_based_edges(memory_node):
    nodes = [
        memory_node("Node 1", meta='{"tags": ["foo"]}', node_id="n1"),
        memory_node("Node 2", meta='{"tags": ["foo", "bar"]}', node_id="n2"),
        memory_node("Node 3", meta='{"tags": ["bar"]}', node_id="n3"),
    ]
    result = extract_tag_based_edges(nodes)
    # n1 <-> n2 share 'foo', n2 <-> n3 share 'bar'
    assert any(e["from_id"] == "n1" and e["to_id"] == "n2" and e["relation_type"] == "shared_tag" for e in result)
    assert any(e["from_id"] == "n2" and e["to_id"] == "n1" and e["relation_type"] == "shared_tag" for e in result)
    assert any(e["from_id"] == "n2" and e["to_id"] == "n3" and e["relation_type"] == "shared_tag" for e in result)
    assert any(e["from_id"] == "n3" and e["to_id"] == "n2" and e["relation_type"] == "shared_tag" for e in result)


def test_extract_content_based_edges(memory_node):
    nodes = [
        memory_node("This references n2", node_id="n1"),
        memory_node("No references", node_id="n2"),
    ]
    result = extract_content_based_edges(nodes)
    assert any(e["from_id"] == "n1" and e["to_id"] == "n2" and e["relation_type"] == "content_ref" for e in result)


def test_extract_custom_edges():
    # Placeholder for future custom rule-based edge extraction
    assert extract_custom_edges([]) == [] 
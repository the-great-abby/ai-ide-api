import pytest
import json

def test_memory_graph_endpoint(client, admin_headers):
    """Test the /memory/graph endpoint."""
    # Test without namespace
    response = client.get("/memory/graph", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "total_nodes" in data
    assert "total_edges" in data
    assert "namespace" in data

def test_memory_visualization_json(client, admin_headers):
    """Test the /memory/visualization endpoint with JSON format."""
    response = client.get("/memory/visualization?format=json", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data

def test_memory_visualization_mermaid(client, admin_headers):
    """Test the /memory/visualization endpoint with Mermaid format."""
    response = client.get("/memory/visualization?format=mermaid", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "mermaid"
    assert "content" in data
    assert "graph_data" in data
    assert data["content"].startswith("graph TD")

def test_memory_visualization_dot(client, admin_headers):
    """Test the /memory/visualization endpoint with DOT format."""
    response = client.get("/memory/visualization?format=dot", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "dot"
    assert "content" in data
    assert "graph_data" in data
    assert data["content"].startswith("digraph MemoryGraph")

def test_memory_export_json(client, admin_headers):
    """Test the /memory/export endpoint with JSON format."""
    response = client.get("/memory/export?format=json", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data

def test_memory_export_csv(client, admin_headers):
    """Test the /memory/export endpoint with CSV format."""
    response = client.get("/memory/export?format=csv", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "csv"
    assert "nodes" in data
    assert "edges" in data
    assert "total_nodes" in data
    assert "total_edges" in data

def test_memory_export_gexf(client, admin_headers):
    """Test the /memory/export endpoint with GEXF format."""
    response = client.get("/memory/export?format=gexf", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "gexf"
    assert "content" in data
    assert "total_nodes" in data
    assert "total_edges" in data
    assert data["content"].startswith('<?xml version="1.0"')

def test_memory_graph_with_namespace(client, admin_headers):
    """Test the /memory/graph endpoint with namespace filter."""
    # Create a test memory first
    memory_data = {
        "namespace": "test_visualization",
        "content": "Test memory for visualization",
        "meta": "{}",
        "categories": ["test"],
        "tags": ["visualization"]
    }
    create_response = client.post("/memory/nodes", json=memory_data, headers=admin_headers)
    assert create_response.status_code == 200
    
    # Test graph with namespace filter
    response = client.get("/memory/graph?namespace=test_visualization", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["namespace"] == "test_visualization"
    assert len(data["nodes"]) >= 1  # Should include our test memory
    
    # Clean up
    memory_id = create_response.json()["id"]
    client.delete(f"/memory/nodes/{memory_id}", headers=admin_headers) 
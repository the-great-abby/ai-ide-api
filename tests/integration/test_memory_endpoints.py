import pytest
import uuid
from fastapi.testclient import TestClient
from rule_api_server import app  # Updated import to match project structure

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def test_namespace():
    return f"test_memory_ns_{uuid.uuid4().hex[:8]}"

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def test_end_to_end_memory_flow(client, admin_headers, test_namespace):
    # 1. Create a memory node
    node1 = {
        "namespace": test_namespace,
        "content": "First node",
        "meta": "{\"type\": \"test\"}"
    }
    resp = client.post("/memory/nodes", json=node1, headers=admin_headers)
    assert resp.status_code == 200, f"Create node1 failed: {resp.text}"
    node1_id = resp.json()["id"]

    # 2. List memory nodes and verify node1 is present
    resp = client.get(f"/memory/nodes?namespace={test_namespace}", headers=admin_headers)
    assert resp.status_code == 200, f"List nodes failed: {resp.text}"
    nodes = resp.json()
    assert any(n["id"] == node1_id for n in nodes), "Node1 not found in list"

    # 3. Create a second node
    node2 = {
        "namespace": test_namespace,
        "content": "Second node",
        "meta": "{\"type\": \"test\"}"
    }
    resp = client.post("/memory/nodes", json=node2, headers=admin_headers)
    assert resp.status_code == 200, f"Create node2 failed: {resp.text}"
    node2_id = resp.json()["id"]

    # 4. Create an edge between the two nodes
    edge = {
        "from_id": node1_id,
        "to_id": node2_id,
        "relation_type": "test_link",
        "meta": "{\"weight\": 1}"
    }
    resp = client.post("/memory/edges", json=edge, headers=admin_headers)
    assert resp.status_code == 200, f"Create edge failed: {resp.text}"
    edge_id = resp.json()["id"]

    # 5. List memory edges and verify the edge is present
    resp = client.get(f"/memory/edges?from_id={node1_id}", headers=admin_headers)
    assert resp.status_code == 200, f"List edges failed: {resp.text}"
    edges = resp.json()
    assert any(e["id"] == edge_id for e in edges), "Edge not found in list"

    # 6. Delete all nodes in the namespace
    resp = client.delete(f"/memory/nodes?namespace={test_namespace}", headers=admin_headers)
    assert resp.status_code == 200, f"Delete nodes failed: {resp.text}"
    assert resp.json()["deleted"] >= 2, "Expected at least 2 nodes deleted"

    # 7. Verify cleanup
    resp = client.get(f"/memory/nodes?namespace={test_namespace}", headers=admin_headers)
    assert resp.status_code == 200, f"List nodes after delete failed: {resp.text}"
    assert len(resp.json()) == 0, "Nodes not deleted" 
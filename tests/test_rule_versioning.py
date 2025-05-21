import pytest
from fastapi.testclient import TestClient
from rule_api_server import app

client = TestClient(app)

def test_rule_versioning_flow():
    # Create initial rule
    initial_rule = {
        "rule_type": "test_versioning",
        "description": "Initial version",
        "diff": "Initial diff",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning"]
    }
    
    # Create and approve initial rule
    prop_response = client.post("/propose-rule-change", json=initial_rule)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    
    # Get the rule ID
    rules = client.get("/rules").json()
    rule = next(r for r in rules if r["description"] == "Initial version")
    rule_id = rule["id"]
    
    # Create a new version
    updated_rule = {
        "rule_type": "test_versioning",
        "description": "Updated version",
        "diff": "Updated diff",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning", "updated"]
    }
    
    # Create and approve update
    prop_response = client.post("/propose-rule-change", json=updated_rule)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    
    # Check version history
    history_response = client.get(f"/rules/{rule_id}/history")
    assert history_response.status_code == 200
    history = history_response.json()
    
    # Should have at least 2 versions
    assert len(history) >= 2
    
    # Verify versions are in correct order (newest first)
    assert history[0]["description"] == "Updated version"
    assert history[1]["description"] == "Initial version"
    
    # Verify version numbers
    assert history[0]["version"] > history[1]["version"]

def test_rule_history_nonexistent():
    # Try to get history for non-existent rule
    response = client.get("/rules/nonexistent-id/history")
    assert response.status_code == 200
    assert response.json() == []

def test_multiple_rule_updates():
    # Create initial rule
    initial_rule = {
        "rule_type": "test_multiple_updates",
        "description": "Version 1",
        "diff": "Diff 1",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning"]
    }
    
    # Create and approve initial rule
    prop_response = client.post("/propose-rule-change", json=initial_rule)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    
    # Get the rule ID
    rules = client.get("/rules").json()
    rule = next(r for r in rules if r["description"] == "Version 1")
    rule_id = rule["id"]
    
    # Create multiple updates
    updates = [
        {
            "rule_type": "test_multiple_updates",
            "description": f"Version {i+2}",
            "diff": f"Diff {i+2}",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["versioning", f"v{i+2}"]
        }
        for i in range(3)  # Create 3 more versions
    ]
    
    for update in updates:
        prop_response = client.post("/propose-rule-change", json=update)
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.post(f"/approve-rule-change/{proposal_id}")
        assert approve_response.status_code == 200
    
    # Check version history
    history_response = client.get(f"/rules/{rule_id}/history")
    assert history_response.status_code == 200
    history = history_response.json()
    
    # Should have 4 versions total
    assert len(history) == 4
    
    # Verify versions are in correct order and have correct content
    for i, version in enumerate(history):
        assert version["description"] == f"Version {4-i}"
        assert version["diff"] == f"Diff {4-i}"
        assert f"v{4-i}" in version["tags"]

def test_rule_version_metadata():
    # Create initial rule with metadata
    initial_rule = {
        "rule_type": "test_metadata",
        "description": "Initial version",
        "diff": "Initial diff",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code"
    }
    
    # Create and approve initial rule
    prop_response = client.post("/propose-rule-change", json=initial_rule)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    
    # Get the rule ID
    rules = client.get("/rules").json()
    rule = next(r for r in rules if r["description"] == "Initial version")
    rule_id = rule["id"]
    
    # Update with new metadata
    updated_rule = {
        "rule_type": "test_metadata",
        "description": "Updated version",
        "diff": "Updated diff",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning", "updated"],
        "examples": ["Example 1", "Example 2"],
        "applies_to": ["python", "javascript"],
        "applies_to_rationale": "For Python and JavaScript code"
    }
    
    # Create and approve update
    prop_response = client.post("/propose-rule-change", json=updated_rule)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    
    # Check version history
    history_response = client.get(f"/rules/{rule_id}/history")
    assert history_response.status_code == 200
    history = history_response.json()
    
    # Verify metadata is preserved in history
    assert len(history) >= 2
    assert history[0]["examples"] == ["Example 1", "Example 2"]
    assert history[0]["applies_to"] == ["python", "javascript"]
    assert history[0]["applies_to_rationale"] == "For Python and JavaScript code"
    
    assert history[1]["examples"] == ["Example 1"]
    assert history[1]["applies_to"] == ["python"]
    assert history[1]["applies_to_rationale"] == "For Python code" 
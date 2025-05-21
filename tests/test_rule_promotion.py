import pytest
from fastapi.testclient import TestClient
from rule_api_server import app

client = TestClient(app)

def test_rule_promotion_flow():
    # First create a rule at project scope
    project_rule = {
        "rule_type": "test_promotion",
        "description": "Test rule for promotion",
        "diff": "Test diff",
        "submitted_by": "tester",
        "scope_level": "project",
        "scope_id": "test-project-1",
        "categories": ["test"],
        "tags": ["promotion"]
    }
    
    # Create the rule through proposal/approval flow
    prop_response = client.post("/propose-rule-change", json=project_rule)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    
    # Approve the proposal
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    
    # Get the rule ID
    rules = client.get("/rules?scope_level=project&scope_id=test-project-1").json()
    rule = next(r for r in rules if r["description"] == "Test rule for promotion")
    rule_id = rule["id"]
    
    # Test promotion to team scope
    team_promotion = {
        "scope_level": "team",
        "scope_id": "test-team-1"
    }
    promote_response = client.post(f"/rules/{rule_id}/promote", json=team_promotion)
    assert promote_response.status_code == 200
    promoted_rule = promote_response.json()
    assert promoted_rule["scope_level"] == "team"
    assert promoted_rule["scope_id"] == "test-team-1"
    
    # Test promotion to global scope
    global_promotion = {
        "scope_level": "global"
    }
    promote_response = client.post(f"/rules/{rule_id}/promote", json=global_promotion)
    assert promote_response.status_code == 200
    promoted_rule = promote_response.json()
    assert promoted_rule["scope_level"] == "global"
    assert promoted_rule["scope_id"] is None

def test_invalid_promotion():
    # Create a rule at team scope
    team_rule = {
        "rule_type": "test_invalid_promotion",
        "description": "Test invalid promotion",
        "diff": "Test diff",
        "submitted_by": "tester",
        "scope_level": "team",
        "scope_id": "test-team-2",
        "categories": ["test"],
        "tags": ["promotion"]
    }
    
    # Create and approve the rule
    prop_response = client.post("/propose-rule-change", json=team_rule)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    
    # Get the rule ID
    rules = client.get("/rules?scope_level=team&scope_id=test-team-2").json()
    rule = next(r for r in rules if r["description"] == "Test invalid promotion")
    rule_id = rule["id"]
    
    # Test invalid promotion (trying to demote to project scope)
    invalid_promotion = {
        "scope_level": "project",
        "scope_id": "test-project-2"
    }
    promote_response = client.post(f"/rules/{rule_id}/promote", json=invalid_promotion)
    assert promote_response.status_code == 400
    assert "Can only promote to a higher scope" in promote_response.json()["detail"]
    
    # Test invalid scope level
    invalid_scope = {
        "scope_level": "invalid_scope",
        "scope_id": "test-id"
    }
    promote_response = client.post(f"/rules/{rule_id}/promote", json=invalid_scope)
    assert promote_response.status_code == 400
    assert "Invalid scope_level" in promote_response.json()["detail"]

def test_promotion_with_missing_scope_id():
    # Create a rule at project scope
    project_rule = {
        "rule_type": "test_missing_scope",
        "description": "Test missing scope ID",
        "diff": "Test diff",
        "submitted_by": "tester",
        "scope_level": "project",
        "scope_id": "test-project-3",
        "categories": ["test"],
        "tags": ["promotion"]
    }
    
    # Create and approve the rule
    prop_response = client.post("/propose-rule-change", json=project_rule)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    
    # Get the rule ID
    rules = client.get("/rules?scope_level=project&scope_id=test-project-3").json()
    rule = next(r for r in rules if r["description"] == "Test missing scope ID")
    rule_id = rule["id"]
    
    # Test promotion to team scope without scope_id
    invalid_promotion = {
        "scope_level": "team"
    }
    promote_response = client.post(f"/rules/{rule_id}/promote", json=invalid_promotion)
    assert promote_response.status_code == 400
    assert "scope_id is required" in promote_response.json()["detail"] 
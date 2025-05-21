import pytest
from fastapi.testclient import TestClient
from rule_api_server import app
import tempfile
import os
import json

client = TestClient(app)

def test_rule_validation_edge_cases():
    # Test empty rule
    empty_rule = {}
    response = client.post("/propose-rule-change", json=empty_rule)
    assert response.status_code == 422
    
    # Test rule with wrong types
    invalid_types_rule = {
        "rule_type": 123,
        "description": None,
        "diff": 456,
        "submitted_by": []
    }
    response = client.post("/propose-rule-change", json=invalid_types_rule)
    assert response.status_code == 422
    
    # Test rule with empty strings
    empty_strings_rule = {
        "rule_type": "",
        "description": "   ",
        "diff": "",
        "submitted_by": "tester"
    }
    response = client.post("/propose-rule-change", json=empty_strings_rule)
    assert response.status_code == 422
    
    # Test rule with invalid MDC format
    invalid_mdc_rule = {
        "rule_type": "test_rule",
        "description": "Test description",
        "diff": "Just some text without proper sections",
        "submitted_by": "tester"
    }
    response = client.post("/propose-rule-change", json=invalid_mdc_rule)
    assert response.status_code == 422

def test_rule_enforcement_error_handling():
    # Test code review with non-existent file
    response = client.post("/review-code-files", files={"files": ("nonexistent.py", b"", "text/x-python")})
    assert response.status_code == 200
    data = response.json()
    assert "nonexistent.py" in data
    assert len(data["nonexistent.py"]) == 0
    
    # Test code review with invalid file type
    response = client.post("/review-code-files", files={"files": ("test.txt", b"some text", "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert "test.txt" not in data
    
    # Test code review with empty file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as py_file:
        py_file.write("")
        py_file.flush()
        py_file.seek(0)
        
        with open(py_file.name, "rb") as f:
            files = {"files": (py_file.name, f, "text/x-python")}
            response = client.post("/review-code-files", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert py_file.name in data or any(k.endswith(".py") for k in data.keys())
        suggestions = data.get(py_file.name, [])
        assert isinstance(suggestions, list)

def test_rule_promotion_edge_cases():
    # Create a base rule
    rule = {
        "rule_type": "test_promotion",
        "description": "Test rule for promotion",
        "diff": """# Rule: Test Promotion
## Description
Test rule for promotion edge cases.
## Enforcement
Testing promotion edge cases.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["promotion"]
    }
    
    # Create and approve the rule
    prop_response = client.post("/propose-rule-change", json=rule)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    rule_id = approve_response.json()["id"]
    
    # Test promotion with invalid scope level
    invalid_scope = {
        "scope_level": "invalid_scope",
        "scope_id": "team-1"
    }
    response = client.post(f"/rules/{rule_id}/promote", json=invalid_scope)
    assert response.status_code == 400
    
    # Test promotion with missing scope_id for team scope
    missing_scope_id = {
        "scope_level": "team"
    }
    response = client.post(f"/rules/{rule_id}/promote", json=missing_scope_id)
    assert response.status_code == 422
    
    # Test promotion of non-existent rule
    response = client.post("/rules/nonexistent-id/promote", json={"scope_level": "team", "scope_id": "team-1"})
    assert response.status_code == 404

def test_rule_versioning_edge_cases():
    # Create initial rule
    rule = {
        "rule_type": "test_versioning",
        "description": "Test rule for versioning",
        "diff": """# Rule: Test Versioning
## Description
Test rule for versioning edge cases.
## Enforcement
Testing versioning edge cases.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning"]
    }
    
    # Create and approve initial version
    prop_response = client.post("/propose-rule-change", json=rule)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    rule_id = approve_response.json()["id"]
    
    # Test history for non-existent rule
    response = client.get("/rules/nonexistent-id/history")
    assert response.status_code == 200
    assert response.json() == []
    
    # Test update with invalid rule_id
    invalid_update = {
        "rule_type": "test_versioning",
        "description": "Updated version",
        "diff": "Updated diff",
        "submitted_by": "tester",
        "rule_id": "nonexistent-id"
    }
    response = client.post("/propose-rule-change", json=invalid_update)
    assert response.status_code == 200  # Proposal created
    proposal_id = response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200  # New rule created instead of updating

def test_rule_feedback_edge_cases():
    # Create a rule proposal
    proposal = {
        "rule_type": "test_feedback",
        "description": "Test rule for feedback",
        "diff": """# Rule: Test Feedback
## Description
Test rule for feedback edge cases.
## Enforcement
Testing feedback edge cases.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["feedback"]
    }
    
    prop_response = client.post("/propose-rule-change", json=proposal)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    
    # Test feedback with empty comments
    empty_feedback = {
        "feedback_type": "suggestion",
        "comments": ""
    }
    response = client.post(f"/api/rule_proposals/{proposal_id}/feedback", json=empty_feedback)
    assert response.status_code == 200
    
    # Test feedback with very long comments
    long_feedback = {
        "feedback_type": "suggestion",
        "comments": "x" * 10000  # Very long comment
    }
    response = client.post(f"/api/rule_proposals/{proposal_id}/feedback", json=long_feedback)
    assert response.status_code == 200
    
    # Test feedback with special characters
    special_chars_feedback = {
        "feedback_type": "suggestion",
        "comments": "!@#$%^&*()_+{}|:\"<>?[]\\;',./~`"
    }
    response = client.post(f"/api/rule_proposals/{proposal_id}/feedback", json=special_chars_feedback)
    assert response.status_code == 200
    
    # Test feedback with HTML/script injection attempt
    injection_feedback = {
        "feedback_type": "suggestion",
        "comments": "<script>alert('xss')</script>"
    }
    response = client.post(f"/api/rule_proposals/{proposal_id}/feedback", json=injection_feedback)
    assert response.status_code == 200
    # Verify the response doesn't contain the script
    feedback_list = client.get(f"/api/rule_proposals/{proposal_id}/feedback").json()
    assert not any("<script>" in f["comments"] for f in feedback_list) 
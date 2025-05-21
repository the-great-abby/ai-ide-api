import pytest
from fastapi.testclient import TestClient
from rule_api_server import app

client = TestClient(app)

def test_submit_and_list_feedback():
    # First create a rule proposal
    proposal = {
        "rule_type": "test_feedback",
        "description": "Test rule for feedback",
        "diff": "Test diff",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["feedback"]
    }
    
    # Create the proposal
    prop_response = client.post("/propose-rule-change", json=proposal)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    
    # Submit feedback
    feedback = {
        "feedback_type": "suggestion",
        "comments": "This rule could be improved by adding more examples."
    }
    feedback_response = client.post(f"/api/rule_proposals/{proposal_id}/feedback", json=feedback)
    assert feedback_response.status_code == 200
    feedback_data = feedback_response.json()
    assert feedback_data["feedback_type"] == "suggestion"
    assert feedback_data["comments"] == "This rule could be improved by adding more examples."
    assert feedback_data["rule_proposal_id"] == proposal_id
    
    # List feedback
    list_response = client.get(f"/api/rule_proposals/{proposal_id}/feedback")
    assert list_response.status_code == 200
    feedback_list = list_response.json()
    assert len(feedback_list) == 1
    assert feedback_list[0]["feedback_type"] == "suggestion"
    assert feedback_list[0]["comments"] == "This rule could be improved by adding more examples."

def test_multiple_feedback_entries():
    # Create a rule proposal
    proposal = {
        "rule_type": "test_multiple_feedback",
        "description": "Test multiple feedback entries",
        "diff": "Test diff",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["feedback"]
    }
    
    prop_response = client.post("/propose-rule-change", json=proposal)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    
    # Submit multiple feedback entries
    feedback_entries = [
        {
            "feedback_type": "suggestion",
            "comments": "First suggestion"
        },
        {
            "feedback_type": "question",
            "comments": "How will this be enforced?"
        },
        {
            "feedback_type": "concern",
            "comments": "This might be too restrictive"
        }
    ]
    
    for feedback in feedback_entries:
        response = client.post(f"/api/rule_proposals/{proposal_id}/feedback", json=feedback)
        assert response.status_code == 200
    
    # List all feedback
    list_response = client.get(f"/api/rule_proposals/{proposal_id}/feedback")
    assert list_response.status_code == 200
    feedback_list = list_response.json()
    assert len(feedback_list) == 3
    
    # Verify all feedback types are present
    feedback_types = {f["feedback_type"] for f in feedback_list}
    assert feedback_types == {"suggestion", "question", "concern"}

def test_feedback_on_nonexistent_proposal():
    # Try to submit feedback for a non-existent proposal
    feedback = {
        "feedback_type": "suggestion",
        "comments": "Test feedback"
    }
    response = client.post("/api/rule_proposals/nonexistent-id/feedback", json=feedback)
    assert response.status_code == 404
    
    # Try to list feedback for a non-existent proposal
    list_response = client.get("/api/rule_proposals/nonexistent-id/feedback")
    assert list_response.status_code == 200
    assert list_response.json() == []

def test_invalid_feedback_type():
    # Create a rule proposal
    proposal = {
        "rule_type": "test_invalid_feedback",
        "description": "Test invalid feedback type",
        "diff": "Test diff",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["feedback"]
    }
    
    prop_response = client.post("/propose-rule-change", json=proposal)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    
    # Submit feedback with invalid type
    invalid_feedback = {
        "feedback_type": "invalid_type",
        "comments": "Test feedback"
    }
    response = client.post(f"/api/rule_proposals/{proposal_id}/feedback", json=invalid_feedback)
    assert response.status_code == 422  # Validation error 
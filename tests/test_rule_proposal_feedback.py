import uuid

import pytest
from fastapi.testclient import TestClient

from rule_api_server import app


def test_submit_and_list_feedback(admin_headers, client, override_get_db):
    # First create a rule proposal
    proposal = {
        "rule_type": "feedback_test",
        "description": "Feedback test rule",
        "diff": "# Rule: Test diff\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["feedback"],
        "scope_level": "project",
        "project": "test-project",
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing feedback flow.",
        "references": "Test reference.",
    }

    # Create the proposal
    prop_response = client.post(
        "/propose-rule-change", json=proposal, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]

    # Submit feedback
    feedback = {
        "feedback_type": "suggestion",
        "comments": "This rule could be improved by adding more examples.",
        "scope_level": "project",
        "project": "test-project",
    }
    feedback_response = client.post(
        f"/api/rule_proposals/{proposal_id}/feedback",
        json=feedback,
        headers=admin_headers,
    )
    assert feedback_response.status_code == 200
    feedback_data = feedback_response.json()
    assert feedback_data["feedback_type"] == "suggestion"
    assert (
        feedback_data["comments"]
        == "This rule could be improved by adding more examples."
    )
    assert feedback_data["rule_proposal_id"] == proposal_id

    # List feedback
    list_response = client.get(
        f"/api/rule_proposals/{proposal_id}/feedback", headers=admin_headers
    )
    assert list_response.status_code == 200
    feedback_list = list_response.json()
    assert len(feedback_list) == 1
    assert feedback_list[0]["feedback_type"] == "suggestion"
    assert feedback_list[0]["comments"] == "This rule could be improved by adding more examples."


def test_multiple_feedback_entries(admin_headers, client, override_get_db):
    # Create a rule proposal
    proposal = {
        "rule_type": "test_multiple_feedback",
        "description": "Test multiple feedback entries",
        "diff": "# Rule: Test diff\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["feedback"],
        "scope_level": "project",
        "project": "test-project",
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing feedback flow.",
        "references": "Test reference.",
    }

    prop_response = client.post(
        "/propose-rule-change", json=proposal, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]

    # Submit multiple feedback entries
    feedback_entries = [
        {"feedback_type": "suggestion", "comments": "First suggestion", "scope_level": "project", "project": "test-project"},
        {"feedback_type": "question", "comments": "How will this be enforced?", "scope_level": "project", "project": "test-project"},
        {"feedback_type": "concern", "comments": "This might be too restrictive", "scope_level": "project", "project": "test-project"},
    ]

    for feedback in feedback_entries:
        response = client.post(
            f"/api/rule_proposals/{proposal_id}/feedback",
            json=feedback,
            headers=admin_headers,
        )
        assert response.status_code == 200

    # List all feedback
    list_response = client.get(
        f"/api/rule_proposals/{proposal_id}/feedback", headers=admin_headers
    )
    assert list_response.status_code == 200
    feedback_list = list_response.json()
    assert len(feedback_list) == 3

    # Verify all feedback types are present
    feedback_types = {f["feedback_type"] for f in feedback_list}
    assert feedback_types == {"suggestion", "question", "concern"}


@pytest.mark.negative
def test_feedback_on_nonexistent_proposal(admin_headers, client, override_get_db):
    # Try to submit feedback for a non-existent proposal
    feedback = {"feedback_type": "suggestion", "comments": "Test feedback", "scope_level": "project", "project": "test-project"}
    fake_id = str(uuid.uuid4())
    response = client.post(
        f"/api/rule_proposals/{fake_id}/feedback", json=feedback, headers=admin_headers
    )
    assert response.status_code == 404
    # Try to list feedback for a non-existent proposal
    list_response = client.get(
        f"/api/rule_proposals/{fake_id}/feedback", headers=admin_headers
    )
    assert list_response.status_code == 404


@pytest.mark.negative
def test_invalid_feedback_type(admin_headers, client, override_get_db):
    # Create a rule proposal
    proposal = {
        "rule_type": "test_invalid_feedback",
        "description": "Test invalid feedback type",
        "diff": "# Rule: Test diff\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["feedback"],
        "scope_level": "project",
        "project": "test-project",
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing feedback flow.",
        "references": "Test reference.",
    }

    prop_response = client.post(
        "/propose-rule-change", json=proposal, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]

    # Submit feedback with invalid type
    invalid_feedback = {"feedback_type": "invalid_type", "comments": "Test feedback", "scope_level": "project", "project": "test-project"}
    response = client.post(
        f"/api/rule_proposals/{proposal_id}/feedback",
        json=invalid_feedback,
        headers=admin_headers,
    )
    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "allowed_types" in data, "Error response should include allowed_types"
    assert set(data["allowed_types"]) == {"suggestion", "question", "concern"}

    # Create the proposal
    prop_response = client.post(
        "/propose-rule-change", json=proposal, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]

    # Approve the proposal
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200


@pytest.mark.parametrize("feedback_type,expected_status", [
    ("suggestion", 200),
    ("question", 200),
    ("concern", 200),
    ("invalid_type", 422),
    ("", 422),
    (None, 422),
    ("ACCEPT", 422),
    ("reject", 422),
])
def test_feedback_type_enforcement(admin_headers, client, feedback_type, expected_status, override_get_db):
    # Create a rule proposal
    proposal = {
        "rule_type": "test_feedback_type_enforcement",
        "description": "Test feedback type enforcement",
        "diff": "# Rule: Test diff\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["feedback"],
        "scope_level": "project",
        "project": "test-project",
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing feedback type enforcement.",
        "references": "Test reference.",
    }
    prop_response = client.post(
        "/propose-rule-change", json=proposal, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    feedback = {"feedback_type": feedback_type, "comments": "Test feedback", "scope_level": "project", "project": "test-project"}
    response = client.post(
        f"/api/rule_proposals/{proposal_id}/feedback",
        json=feedback,
        headers=admin_headers,
    )
    assert response.status_code == expected_status
    if expected_status == 422:
        data = response.json()
        assert "allowed_types" in data, "Error response should include allowed_types"
        assert set(data["allowed_types"]) == {"suggestion", "question", "concern"}

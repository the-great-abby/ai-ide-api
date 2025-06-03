import uuid

import pytest
from fastapi.testclient import TestClient

from rule_api_server import app

client = TestClient(app)


@pytest.mark.unit
def test_basic_rule_update(admin_headers):
    # Create initial rule
    initial_rule = {
        "rule_type": "test_update",
        "description": "Initial rule",
        "diff": "# Rule: test_update\n## Description\nInitial rule\n## Enforcement\nThis rule is enforced through automated testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["update"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing update flow.",
        "references": "Test reference.",
    }

    # Create and approve initial rule
    prop_response = client.post(
        "/propose-rule-change", json=initial_rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Get the rule ID
    rules = client.get("/rules", headers=admin_headers).json()
    rule = next(r for r in rules if r["description"] == "Initial rule")
    rule_id = rule["id"]

    # Update the rule
    update_data = {
        "description": "Updated rule",
        "categories": ["test", "updated"],
        "tags": ["update", "modified"],
        "examples": ["Example 2"],
        "applies_to": ["python", "updated_python"],
    }
    update_response = client.patch(
        f"/rules/{rule_id}", json=update_data, headers=admin_headers
    )
    assert update_response.status_code == 200
    updated_rule = update_response.json()

    # Verify updates
    assert updated_rule["description"] == "Updated rule"
    assert set(updated_rule["categories"]) == {"test", "updated"}
    assert set(updated_rule["tags"]) == {"update", "modified"}
    assert updated_rule["examples"] == ["Example 2"]
    assert updated_rule["applies_to"] == ["python", "updated_python"]

    # Verify original fields are preserved
    assert updated_rule["rule_type"] == "test_update"
    assert (
        updated_rule["diff"]
        == "# Rule: test_update\n## Description\nInitial rule\n## Enforcement\nThis rule is enforced through automated testing."
    )
    assert updated_rule["submitted_by"] == "tester"


@pytest.mark.unit
def test_partial_rule_update(admin_headers):
    # Create initial rule
    initial_rule = {
        "rule_type": "test_partial",
        "description": "Initial rule",
        "diff": "# Rule: test_partial\n## Description\nInitial rule\n## Enforcement\nThis rule is enforced through automated testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["update"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing update flow.",
        "references": "Test reference.",
    }

    # Create and approve initial rule
    prop_response = client.post(
        "/propose-rule-change", json=initial_rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Get the rule ID
    rules = client.get("/rules", headers=admin_headers).json()
    rule = next(r for r in rules if r["description"] == "Initial rule")
    rule_id = rule["id"]

    # Update only description
    update_data = {"description": "Updated description only"}
    update_response = client.patch(
        f"/rules/{rule_id}", json=update_data, headers=admin_headers
    )
    assert update_response.status_code == 200
    updated_rule = update_response.json()

    # Verify only description was updated
    assert updated_rule["description"] == "Updated description only"
    assert updated_rule["categories"] == ["test"]
    assert updated_rule["tags"] == ["update"]
    assert updated_rule["examples"] == ["Example 1"]
    assert updated_rule["applies_to"] == ["python"]
    assert updated_rule["applies_to_rationale"] == "For Python code"


@pytest.mark.negative
def test_update_nonexistent_rule(admin_headers):
    # Try to update non-existent rule
    fake_id = str(uuid.uuid4())
    response = client.patch(
        f"/rules/{fake_id}", json={"description": "Updated rule"}, headers=admin_headers
    )
    assert response.status_code == 404


@pytest.mark.negative
def test_update_with_invalid_data(admin_headers):
    # Create initial rule
    initial_rule = {
        "rule_type": "test_invalid",
        "description": "Initial rule",
        "diff": "# Rule: test_invalid\n## Description\nInitial rule\n## Enforcement\nThis rule is enforced through automated testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["update"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing update flow.",
        "references": "Test reference.",
    }

    # Create and approve initial rule
    prop_response = client.post(
        "/propose-rule-change", json=initial_rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Get the rule ID
    rules = client.get("/rules", headers=admin_headers).json()
    rule = next(r for r in rules if r["description"] == "Initial rule")
    rule_id = rule["id"]

    # Try to update with invalid data
    invalid_updates = [
        {"rule_type": None},  # None value
        {"description": ""},  # Empty string
        {"categories": None},  # None value
        {"tags": []},  # Empty list
        {"invalid_field": "value"},  # Invalid field
    ]

    for invalid_update in invalid_updates:
        response = client.patch(
            f"/rules/{rule_id}", json=invalid_update, headers=admin_headers
        )
        assert response.status_code in [
            400,
            422,
        ]  # Either validation error or bad request


@pytest.mark.negative
def test_update_immutable_fields(admin_headers):
    # Create initial rule
    initial_rule = {
        "rule_type": "test_immutable",
        "description": "Initial rule",
        "diff": "# Rule: test_immutable\n## Description\nInitial rule\n## Enforcement\nThis rule is enforced through automated testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["update"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing update flow.",
        "references": "Test reference.",
    }

    # Create and approve initial rule
    prop_response = client.post(
        "/propose-rule-change", json=initial_rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Get the rule ID
    rules = client.get("/rules", headers=admin_headers).json()
    rule = next(r for r in rules if r["description"] == "Initial rule")
    rule_id = rule["id"]

    # Try to update immutable fields
    immutable_updates = [
        {"rule_type": "new_type"},  # Should not be changeable
        {"submitted_by": "new_user"},  # Should not be changeable
        {"version": 2},  # Should not be changeable
        {"id": "new_id"},  # Should not be changeable
    ]

    for immutable_update in immutable_updates:
        response = client.patch(
            f"/rules/{rule_id}", json=immutable_update, headers=admin_headers
        )
        assert response.status_code in [
            400,
            422,
        ]  # Either validation error or bad request

        # Verify the field was not changed
        rule_response = client.get(f"/rules/{rule_id}", headers=admin_headers)
        assert rule_response.status_code == 200
        current_rule = rule_response.json()
        for field, value in immutable_update.items():
            assert current_rule[field] != value

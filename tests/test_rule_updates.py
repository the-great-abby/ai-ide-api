import uuid

import pytest

from rule_api_server import app


@pytest.mark.unit
def test_basic_rule_update(admin_headers, client, override_get_db):
    # Create initial rule
    initial_rule = {
        "rule_type": "test_update",
        "description": "Initial rule",
        "diff": "# Rule: test_update\n## Description\nInitial rule\n## Enforcement\nThis rule is enforced through automated testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["update"],
        "scope_level": "project",
        "project": "test-project",
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
    if prop_response.status_code != 200:
        print("RESPONSE BODY:", prop_response.text)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    if approve_response.status_code != 200:
        print("RESPONSE BODY:", approve_response.text)
    assert approve_response.status_code == 200

    # Get the rule ID
    rules = client.get("/rules", headers=admin_headers).json()
    rule = next(r for r in rules if r["description"] == "Initial rule")
    rule_id = rule["id"]

    # PATCH/update payloads: only include fields accepted by the update endpoint
    update_payload = {
        "description": "Updated rule",
        "diff": "# Rule: test_update\n## Description\nUpdated rule\n## Enforcement\nThis rule is enforced through automated testing.",
        "examples": ["Example 2"],
        "applies_to": ["python", "updated_python"],
    }
    update_response = client.patch(
        f"/rules/{rule_id}", json=update_payload, headers=admin_headers
    )
    assert update_response.status_code == 200
    updated_rule = update_response.json()
    assert updated_rule["description"] == "Updated rule"
    assert updated_rule["examples"] == ["Example 2"]
    assert updated_rule["applies_to"] == ["python", "updated_python"]

    # Verify original fields are preserved
    assert updated_rule["rule_type"] == "test_update"
    assert updated_rule["submitted_by"] == "tester"


@pytest.mark.unit
def test_partial_rule_update(admin_headers, client, override_get_db):
    # Create initial rule
    initial_rule = {
        "rule_type": "test_partial",
        "description": "Initial rule",
        "diff": "# Rule: test_partial\n## Description\nInitial rule\n## Enforcement\nThis rule is enforced through automated testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["update"],
        "scope_level": "project",
        "project": "test-project",
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
    if prop_response.status_code != 200:
        print("RESPONSE BODY:", prop_response.text)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    if approve_response.status_code != 200:
        print("RESPONSE BODY:", approve_response.text)
    assert approve_response.status_code == 200

    # Get the rule ID
    rules = client.get("/rules", headers=admin_headers).json()
    rule = next(r for r in rules if r["description"] == "Initial rule")
    rule_id = rule["id"]

    # PATCH/update payloads: only include fields accepted by the update endpoint
    partial_update = {
        "description": "Updated complex rule",
        "applies_to": ["python", "javascript", "typescript"],
    }
    response = client.patch(f"/rules/{rule_id}", json=partial_update, headers=admin_headers)
    assert response.status_code == 200
    updated_rule = response.json()
    assert updated_rule["description"] == "Updated complex rule"
    assert set(updated_rule["applies_to"]) == {"python", "javascript", "typescript"}


@pytest.mark.negative
def test_update_nonexistent_rule(admin_headers, client, override_get_db):
    # Try to update non-existent rule
    fake_id = str(uuid.uuid4())
    response = client.patch(
        f"/rules/{fake_id}", json={"description": "Updated rule"}, headers=admin_headers
    )
    if response.status_code != 404:
        print("RESPONSE BODY:", response.text)
    assert response.status_code == 404


@pytest.mark.negative
def test_update_with_invalid_data(admin_headers, client, override_get_db):
    # Create initial rule
    initial_rule = {
        "rule_type": "test_invalid",
        "description": "Initial rule",
        "diff": "# Rule: test_invalid\n## Description\nInitial rule\n## Enforcement\nThis rule is enforced through automated testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["update"],
        "scope_level": "project",
        "project": "test-project",
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
    if prop_response.status_code != 200:
        print("RESPONSE BODY:", prop_response.text)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    if approve_response.status_code != 200:
        print("RESPONSE BODY:", approve_response.text)
    assert approve_response.status_code == 200

    # Get the rule ID
    rules = client.get("/rules", headers=admin_headers).json()
    rule = next(r for r in rules if r["description"] == "Initial rule")
    rule_id = rule["id"]

    # Try to update with invalid data
    invalid_updates = [
        {"rule_type": None},  # None value (should be 422)
        {"description": ""},  # Empty string (should be 422)
        {"categories": None},  # None value (should be 422)
        {"tags": []},  # Empty list (should be 200)
        {"invalid_field": "value"},  # Invalid field (should be 422)
    ]

    for invalid_update in invalid_updates:
        response = client.patch(
            f"/rules/{rule_id}", json=invalid_update, headers=admin_headers
        )
        # tags: [] is valid, all others should be 422
        if "tags" in invalid_update and invalid_update["tags"] == []:
            if response.status_code != 200:
                print("RESPONSE BODY:", response.text)
            assert response.status_code == 200
        else:
            if response.status_code != 422:
                print("RESPONSE BODY:", response.text)
            assert response.status_code == 422


@pytest.mark.negative
def test_update_immutable_fields(admin_headers, client, override_get_db):
    # Create initial rule
    initial_rule = {
        "rule_type": "test_immutable",
        "description": "Initial rule",
        "diff": "# Rule: test_immutable\n## Description\nInitial rule\n## Enforcement\nThis rule is enforced through automated testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["update"],
        "scope_level": "project",
        "project": "test-project",
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
    if prop_response.status_code != 200:
        print("RESPONSE BODY:", prop_response.text)
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    if approve_response.status_code != 200:
        print("RESPONSE BODY:", approve_response.text)
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
        if response.status_code != 422:
            print("RESPONSE BODY:", response.text)
        assert response.status_code == 422

        # Verify the field was not changed
        rule_response = client.get(f"/rules/{rule_id}", headers=admin_headers)
        assert rule_response.status_code == 200
        current_rule = rule_response.json()
        for field, value in immutable_update.items():
            assert current_rule[field] != value

    # Update rule_type (now allowed)
    update_request = {"rule_type": "updated_type"}
    response = client.patch(f"/rules/{rule_id}", json=update_request, headers=admin_headers)
    assert response.status_code == 200
    updated_rule = response.json()
    assert updated_rule["rule_type"] == "updated_type"

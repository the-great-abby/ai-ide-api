import uuid

import pytest
from fastapi.testclient import TestClient

from rule_api_server import app


@pytest.mark.unit
def test_rule_versioning_flow(admin_headers, client, override_get_db):
    # Create initial rule
    initial_rule = {
        "rule_type": "test_versioning",
        "description": "Initial version",
        "diff": "# Rule: Initial diff\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning"],
        "scope_level": "project",
        "project": "test-project",
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing versioning flow.",
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
    rule = next(r for r in rules if r["description"] == "Initial version")
    rule_id = rule["id"]

    # Create a new version
    updated_rule = {
        "rule_type": "test_versioning",
        "description": "Updated version",
        "diff": "# Rule: Updated diff\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning", "updated"],
        "scope_level": "project",
        "project": "test-project",
        "examples": ["Example 1", "Example 2"],
        "applies_to": ["python", "javascript"],
        "applies_to_rationale": "For Python and JavaScript code",
        "parent_rule_id": rule_id,
        "user_story": "Test user story",
        "reason_for_change": "Testing versioning flow.",
        "references": "Test reference.",
    }

    # Create and approve update
    prop_response = client.post(
        "/propose-rule-change", json=updated_rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Check version history
    history_response = client.get(f"/rules/{rule_id}/history", headers=admin_headers)
    assert history_response.status_code == 200
    history = history_response.json()

    # Should have at least 2 versions
    assert len(history) >= 2

    # Verify versions are in correct order (newest first)
    assert history[0]["description"] == "Updated version"
    assert history[1]["description"] == "Initial version"

    # Verify version numbers
    assert history[0]["version"] > history[1]["version"]

    # Verify metadata is preserved in history
    assert len(history) >= 2
    assert history[0]["examples"] == ["Example 1", "Example 2"]
    assert history[0]["applies_to"] == ["python", "javascript"]
    assert history[0]["applies_to_rationale"] == "For Python and JavaScript code"

    assert history[1]["examples"] == ["Example 1"]
    assert history[1]["applies_to"] == ["python"]
    assert history[1]["applies_to_rationale"] == "For Python code"


@pytest.mark.unit
@pytest.mark.negative
def test_rule_history_nonexistent(admin_headers, client, override_get_db):
    # Try to get history for non-existent rule (valid UUID)
    fake_id = str(uuid.uuid4())
    response = client.get(f"/rules/{fake_id}/history", headers=admin_headers)
    assert response.status_code == 404

    # Try to get history for invalid UUID
    invalid_id = "not-a-uuid"
    response = client.get(f"/rules/{invalid_id}/history", headers=admin_headers)
    assert response.status_code == 422


@pytest.mark.unit
def test_multiple_rule_updates(admin_headers, client, override_get_db):
    # Create initial rule
    initial_rule = {
        "rule_type": "test_multiple_updates",
        "description": "Version 1",
        "diff": "# Rule: Diff 1\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning"],
        "scope_level": "project",
        "project": "test-project",
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "user_story": "Test user story",
        "reason_for_change": "Testing multiple updates.",
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
    rule = next(r for r in rules if r["description"] == "Version 1")
    rule_id = rule["id"]

    # Create multiple updates
    updates = [
        {
            "rule_type": "test_multiple_updates",
            "description": f"Version {i+2}",
            "diff": f"# Rule: Diff {i+2}\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["versioning", f"v{i+2}"],
            "parent_rule_id": rule_id,
            "examples": ["Example 1"],
            "applies_to": ["python"],
            "user_story": "Test user story",
            "reason_for_change": f"Testing multiple updates. Reason for change: {f'v{i+2}'}",
            "references": "Test reference.",
            "scope_level": "project",
            "project": "test-project",
        }
        for i in range(3)  # Create 3 more versions
    ]

    for update in updates:
        prop_response = client.post(
            "/propose-rule-change", json=update, headers=admin_headers
        )
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.put(
            f"/rule-changes/{proposal_id}/approve", headers=admin_headers
        )
        assert approve_response.status_code == 200

    # Check version history
    history_response = client.get(f"/rules/{rule_id}/history", headers=admin_headers)
    assert history_response.status_code == 200
    history = history_response.json()

    # Should have 4 versions total
    assert len(history) == 4

    # Verify versions are in correct order and have correct content
    expected_tags = [
        ["versioning", "v4"],
        ["versioning", "v3"],
        ["versioning", "v2"],
        ["versioning"],
    ]
    for i, version in enumerate(history):
        assert version["description"] == f"Version {4-i}"
        assert version["diff"] == f"# Rule: Diff {4-i}\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing."
        assert set(version["tags"]) == set(expected_tags[i])


@pytest.mark.unit
def test_rule_version_metadata(admin_headers, client, override_get_db):
    # Create initial rule with metadata
    initial_rule = {
        "rule_type": "test_metadata",
        "description": "Initial version",
        "diff": "# Rule: Initial diff\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning"],
        "scope_level": "project",
        "project": "test-project",
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing versioning flow.",
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
    rule = next(r for r in rules if r["description"] == "Initial version")
    rule_id = rule["id"]

    # Update with new metadata
    updated_rule = {
        "rule_type": "test_metadata",
        "description": "Updated version",
        "diff": "# Rule: Updated diff\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning", "updated"],
        "examples": ["Example 1", "Example 2"],
        "applies_to": ["python", "javascript"],
        "applies_to_rationale": "For Python and JavaScript code",
        "parent_rule_id": rule_id,
        "user_story": "Test user story",
        "reason_for_change": "Testing versioning flow.",
        "references": "Test reference.",
        "scope_level": "project",
        "project": "test-project",
    }

    # Create and approve update
    prop_response = client.post(
        "/propose-rule-change", json=updated_rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Check version history
    history_response = client.get(f"/rules/{rule_id}/history", headers=admin_headers)
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

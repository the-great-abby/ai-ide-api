import uuid

import pytest
from fastapi.testclient import TestClient

from rule_api_server import app


def test_rule_promotion_flow(admin_headers, client, override_get_db):
    # First create a rule at project scope
    project_rule = {
        "rule_type": "promotion_test",
        "description": "Promotion test rule",
        "diff": "# Rule: Promotion Test\n## Description\nPromotion test rule\n## Enforcement\nTesting promotion.",
        "submitted_by": "tester",
        "scope_level": "project",
        "project": "test-project",
        "categories": ["test"],
        "tags": ["promotion"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing promotion flow.",
        "references": "Test reference.",
    }

    # Create the rule through proposal/approval flow
    prop_response = client.post(
        "/propose-rule-change", json=project_rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]

    # Approve the proposal
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200
    # Always fetch the rule from /rules after approval
    rules = client.get(
        f"/rules?scope_level=project&scope_id={project_rule['project']}", headers=admin_headers
    ).json()
    rule = next(r for r in rules if r["description"] == "Promotion test rule")
    rule_id = rule["id"]

    # Test promotion to team scope
    team_promotion = {"scope_level": "team", "team": "test-team"}
    promote_response = client.post(
        f"/rules/{rule_id}/promote", json=team_promotion, headers=admin_headers
    )
    assert promote_response.status_code == 200
    promoted_rule = promote_response.json()
    assert promoted_rule["scope_level"] == "team"
    assert promoted_rule["scope_id"] is not None

    # Test promotion to global scope
    global_promotion = {"scope_level": "global"}
    promote_response = client.post(
        f"/rules/{rule_id}/promote", json=global_promotion, headers=admin_headers
    )
    assert promote_response.status_code == 200
    promoted_rule = promote_response.json()
    assert promoted_rule["scope_level"] == "global"
    assert promoted_rule["scope_id"] is None


def test_invalid_promotion(admin_headers, client, override_get_db):
    # Create a rule at team scope
    team_scope_id = str(uuid.uuid4())
    team_rule = {
        "rule_type": "test_invalid_promotion",
        "description": "Test invalid promotion",
        "diff": "Test diff",
        "submitted_by": "tester",
        "scope_level": "team",
        "scope_id": team_scope_id,
        "categories": ["test"],
        "tags": ["promotion"],
        "examples": ["Example 2"],
        "applies_to": ["java"],
        "applies_to_rationale": "For Java code",
        "user_story": "Test user story 2",
        "reason_for_change": "Testing invalid promotion.",
        "references": "Test reference 2.",
    }

    # Create and approve the rule
    prop_response = client.post(
        "/propose-rule-change", json=team_rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Get the rule ID using the actual scope_id
    rules = client.get(
        f"/rules?scope_level=team&scope_id={team_scope_id}", headers=admin_headers
    ).json()
    rule = next(r for r in rules if r["description"] == "Test invalid promotion")
    rule_id = rule["id"]

    # Test invalid promotion (trying to demote to project scope)
    invalid_promotion = {"scope_level": "project", "scope_id": "test-project-2"}
    promote_response = client.post(
        f"/rules/{rule_id}/promote", json=invalid_promotion, headers=admin_headers
    )
    if promote_response.status_code != 400:
        print("RESPONSE BODY:", promote_response.text)
    assert promote_response.status_code == 400
    assert "Can only promote to a higher scope" in promote_response.json()["detail"]

    # Test invalid scope level
    invalid_scope = {"scope_level": "invalid_scope", "scope_id": "test-id"}
    promote_response = client.post(
        f"/rules/{rule_id}/promote", json=invalid_scope, headers=admin_headers
    )
    if promote_response.status_code != 400:
        print("RESPONSE BODY:", promote_response.text)
    assert promote_response.status_code == 400
    assert "Invalid scope_level" in promote_response.json()["detail"]


def test_promotion_with_missing_scope_id(admin_headers, client, override_get_db):
    # Create a rule at project scope
    project_scope_id = str(uuid.uuid4())
    project_rule = {
        "rule_type": "test_missing_scope",
        "description": "Test missing scope ID",
        "diff": "Test diff",
        "submitted_by": "tester",
        "scope_level": "project",
        "scope_id": project_scope_id,
        "categories": ["test"],
        "tags": ["promotion"],
        "examples": ["Example 3"],
        "applies_to": ["c++"],
        "applies_to_rationale": "For C++ code",
        "user_story": "Test user story 3",
        "reason_for_change": "Testing missing scope ID.",
        "references": "Test reference 3.",
    }

    # Create and approve the rule
    prop_response = client.post(
        "/propose-rule-change", json=project_rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Get the rule ID using the actual scope_id
    rules = client.get(
        f"/rules?scope_level=project&scope_id={project_scope_id}", headers=admin_headers
    ).json()
    rule = next(r for r in rules if r["description"] == "Test missing scope ID")
    rule_id = rule["id"]

    # Test promotion to team scope without scope_id
    invalid_promotion = {"scope_level": "team"}
    promote_response = client.post(
        f"/rules/{rule_id}/promote", json=invalid_promotion, headers=admin_headers
    )
    if promote_response.status_code != 422:
        print("RESPONSE BODY:", promote_response.text)
    assert promote_response.status_code == 422
    detail = promote_response.json()["detail"].lower()
    assert "scope_id" in detail and "required" in detail

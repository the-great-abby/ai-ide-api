import json
import os
import subprocess
import tempfile
from typing import Dict, List

import pytest

from db import ApiAccessToken, get_db

# @pytest.fixture(autouse=True)
# def clean_tokens(real_db_session):
#     # Delete all existing tokens
#     real_db_session.query(ApiAccessToken).delete()
#     real_db_session.commit()
#     yield
#     real_db_session.close()


def test_rule_conflict_detection(client, admin_headers, override_get_db):
    # Create two conflicting rules
    rule1 = {
        "rule_type": "conflict_test",
        "description": "Test rule 1",
        "diff": "Pattern: def test_function():\nMessage: Test message 1\nSeverity: warning",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    rule2 = {
        "rule_type": "conflict_test",
        "description": "Test rule 2",
        "diff": "Pattern: def another_function():\nMessage: Test message 2\nSeverity: error",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 2"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    # Submit first rule
    response1 = client.post("/propose-rule-change", json=rule1, headers=admin_headers)
    assert response1.status_code == 200
    proposal_id1 = response1.json()["id"]

    # Submit second rule
    response2 = client.post("/propose-rule-change", json=rule2, headers=admin_headers)
    assert response2.status_code == 200
    proposal_id2 = response2.json()["id"]

    # Approve first rule
    approve_response = client.put(
        f"/rule-changes/{proposal_id1}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Try to approve second rule (should fail due to conflict)
    approve_response2 = client.put(
        f"/rule-changes/{proposal_id2}/approve", headers=admin_headers
    )
    assert approve_response2.status_code == 400
    assert "conflict" in approve_response2.json()["detail"].lower()


def test_rule_scope_conflicts(client, admin_headers, override_get_db):
    # Create a rule at team scope
    team_rule = {
        "rule_type": "test_scope_conflict",
        "description": "Team rule",
        "diff": """# Rule: test_scope_conflict
## Description
Team rule description.
## Enforcement
Team rule enforcement.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["scope"],
        "scope_level": "team",
        "scope_id": "team-1",
        "examples": ["Example 1"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing scope flow.",
        "references": "Test reference.",
    }

    # Create a conflicting rule at global scope
    global_rule = {
        "rule_type": "test_scope_conflict",
        "description": "Global rule",
        "diff": """# Rule: test_scope_conflict
## Description
Global rule description.
## Enforcement
Global rule enforcement.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["scope"],
        "scope_level": "global",
        "examples": ["Example 1"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing scope flow.",
        "references": "Test reference.",
    }

    # Submit and approve team rule
    team_response = client.post(
        "/propose-rule-change", json=team_rule, headers=admin_headers
    )
    assert team_response.status_code == 200
    team_proposal_id = team_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{team_proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Submit and try to approve global rule (should fail due to scope conflict)
    global_response = client.post(
        "/propose-rule-change", json=global_rule, headers=admin_headers
    )
    assert global_response.status_code == 200
    global_proposal_id = global_response.json()["id"]
    approve_response2 = client.put(
        f"/rule-changes/{global_proposal_id}/approve", headers=admin_headers
    )
    assert approve_response2.status_code == 400
    assert "scope" in approve_response2.json()["detail"].lower()


def test_rule_enforcement_in_ci(client, admin_headers, override_get_db):
    # Create a test rule
    rule = {
        "rule_type": "test_ci_enforcement",
        "description": "CI enforcement test",
        "diff": """# Rule: test_ci_enforcement
## Description
Test rule for CI enforcement.
## Enforcement
This rule must be enforced in CI.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["ci"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing CI enforcement flow.",
        "references": "Test reference.",
    }

    # Submit and approve the rule
    response = client.post("/propose-rule-change", json=rule, headers=admin_headers)
    assert response.status_code == 200
    proposal_id = response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Create a test file that violates the rule
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write("print('violating rule')")
        f.flush()

        # Run rule enforcement in CI mode
        response = client.post(
            "/review-code-files",
            files={"files": (f.name, open(f.name, "rb"), "text/x-python")},
            headers={"X-CI-Mode": "true", **admin_headers},
        )
        assert response.status_code == 200
        data = response.json()
        assert f.name in data
        suggestions = data[f.name]
        assert len(suggestions) > 0
        assert any(s["rule_type"] == "test_ci_enforcement" for s in suggestions)


def test_rule_violation_reporting(client, admin_headers, override_get_db):
    # Create a test rule
    rule = {
        "rule_type": "test_violation_reporting",
        "description": "Violation reporting test",
        "diff": """# Rule: test_violation_reporting
## Description
Test rule for violation reporting.
## Enforcement
This rule must be reported when violated.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["reporting"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing violation reporting flow.",
        "references": "Test reference.",
    }

    # Submit and approve the rule
    response = client.post("/propose-rule-change", json=rule, headers=admin_headers)
    assert response.status_code == 200
    proposal_id = response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200

    # Create a test file that violates the rule
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write("print('violating rule')")
        f.flush()

        # Get violation report
        response = client.post(
            "/review-code-files",
            files={"files": (f.name, open(f.name, "rb"), "text/x-python")},
            headers={"X-Report-Violations": "true", **admin_headers},
        )
        assert response.status_code == 200
        data = response.json()
        assert f.name in data
        violations = data[f.name]
        assert len(violations) > 0
        assert any(v["rule_type"] == "test_violation_reporting" for v in violations)

        # Verify violation details
        violation = next(
            v for v in violations if v["rule_type"] == "test_violation_reporting"
        )
        assert "description" in violation
        assert "diff" in violation
        assert "line_number" in violation
        assert "severity" in violation


def test_rule_compliance_report(client, admin_headers, override_get_db):
    # Create multiple test rules
    rules = [
        {
            "rule_type": f"test_compliance_{i}",
            "description": f"Compliance test rule {i}",
            "diff": f"""# Rule: test_compliance_{i}
## Description
Test rule {i} for compliance reporting.
## Enforcement
This rule must be included in compliance reports.""",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["compliance"],
            "applies_to_rationale": "For Python code",
            "user_story": "Test user story",
            "reason_for_change": "Testing compliance reporting flow.",
            "references": "Test reference.",
        }
        for i in range(3)
    ]

    # Submit and approve all rules
    for rule in rules:
        response = client.post("/propose-rule-change", json=rule, headers=admin_headers)
        assert response.status_code == 200
        proposal_id = response.json()["id"]
        approve_response = client.put(
            f"/rule-changes/{proposal_id}/approve", headers=admin_headers
        )
        assert approve_response.status_code == 200

    # Get compliance report
    response = client.get("/rules/compliance-report", headers=admin_headers)
    assert response.status_code == 200
    report = response.json()

    # Verify report structure
    assert "total_rules" in report
    assert "compliant_rules" in report
    assert "violations" in report
    assert "summary" in report

    # Verify all test rules are included
    rule_types = {r["rule_type"] for r in report["compliant_rules"]}
    assert all(f"test_compliance_{i}" in rule_types for i in range(3))


def test_rule_conflicts(client, admin_headers, override_get_db):
    # Create conflicting rules
    rule1 = {
        "rule_type": "conflict_test",
        "description": "Test rule 1",
        "diff": "Pattern: def test_function():\nMessage: Test message 1\nSeverity: warning",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    rule2 = {
        "rule_type": "conflict_test",
        "description": "Test rule 2",
        "diff": "Pattern: def test_function():\nMessage: Test message 2\nSeverity: error",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 2"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    # Add first rule
    response = client.post("/propose-rule-change", json=rule1, headers=admin_headers)
    assert response.status_code == 200
    rule1_id = response.json()["id"]

    # Approve first rule
    response = client.put(f"/rule-changes/{rule1_id}/approve", headers=admin_headers)
    assert response.status_code == 200

    # Try to add conflicting rule
    response = client.post("/propose-rule-change", json=rule2, headers=admin_headers)
    assert response.status_code == 422
    assert "conflict" in response.json()["detail"].lower()


def test_rule_conflicts_different_patterns(client, admin_headers, override_get_db):
    # Create rules with different patterns
    rule1 = {
        "rule_type": "conflict_test",
        "description": "Test rule 1",
        "diff": "Pattern: def test_function():\nMessage: Test message 1\nSeverity: warning",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    rule2 = {
        "rule_type": "conflict_test",
        "description": "Test rule 2",
        "diff": "Pattern: def another_function():\nMessage: Test message 2\nSeverity: error",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 2"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    # Add first rule
    response = client.post("/propose-rule-change", json=rule1, headers=admin_headers)
    assert response.status_code == 200
    rule1_id = response.json()["id"]

    # Approve first rule
    response = client.put(f"/rule-changes/{rule1_id}/approve", headers=admin_headers)
    assert response.status_code == 200

    # Add second rule (should succeed)
    response = client.post("/propose-rule-change", json=rule2, headers=admin_headers)
    assert response.status_code == 200
    rule2_id = response.json()["id"]

    # Approve second rule
    response = client.put(f"/rule-changes/{rule2_id}/approve", headers=admin_headers)
    assert response.status_code == 200


def test_rule_conflicts_same_name(client, admin_headers, override_get_db):
    # Create rules with same name but different patterns
    rule1 = {
        "rule_type": "conflict_test",
        "description": "Test rule 1",
        "diff": "Pattern: def test_function():\nMessage: Test message 1\nSeverity: warning",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    rule2 = {
        "rule_type": "conflict_test",
        "description": "Test rule 2",
        "diff": "Pattern: def another_function():\nMessage: Test message 2\nSeverity: error",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 2"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    # Add first rule
    response = client.post("/propose-rule-change", json=rule1, headers=admin_headers)
    assert response.status_code == 200
    rule1_id = response.json()["id"]

    # Approve first rule
    response = client.put(f"/rule-changes/{rule1_id}/approve", headers=admin_headers)
    assert response.status_code == 200

    # Try to add second rule (should fail due to same name)
    response = client.post("/propose-rule-change", json=rule2, headers=admin_headers)
    assert response.status_code == 422
    assert "name" in response.json()["detail"].lower()


def test_rule_conflicts_update(client, admin_headers, override_get_db):
    # Create initial rule
    rule = {
        "rule_type": "conflict_test",
        "description": "Test rule",
        "diff": "Pattern: def test_function():\nMessage: Test message\nSeverity: warning",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    # Add rule
    response = client.post("/propose-rule-change", json=rule, headers=admin_headers)
    assert response.status_code == 200
    rule_id = response.json()["id"]

    # Approve rule
    response = client.put(f"/rule-changes/{rule_id}/approve", headers=admin_headers)
    assert response.status_code == 200

    # Try to update rule with conflicting pattern
    updated_rule = {
        "rule_type": "conflict_test",
        "description": "Updated test rule",
        "diff": "Pattern: def another_function():\nMessage: Updated test message\nSeverity: error",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 2"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    response = client.put(
        f"/update-rule/{rule_id}", json=updated_rule, headers=admin_headers
    )
    assert response.status_code == 422
    assert "conflict" in response.json()["detail"].lower()


def test_rule_conflicts_delete(client, admin_headers, override_get_db):
    # Create initial rule
    rule = {
        "rule_type": "conflict_test",
        "description": "Test rule",
        "diff": "Pattern: def test_function():\nMessage: Test message\nSeverity: warning",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing conflict flow.",
        "references": "Test reference.",
    }

    # Add rule
    response = client.post("/propose-rule-change", json=rule, headers=admin_headers)
    assert response.status_code == 200
    rule_id = response.json()["id"]

    # Approve rule
    response = client.put(f"/rule-changes/{rule_id}/approve", headers=admin_headers)
    assert response.status_code == 200

    # Delete rule
    response = client.delete(f"/delete-rule/{rule_id}", headers=admin_headers)
    assert response.status_code == 200

    # Try to add conflicting rule (should succeed since original rule is deleted)
    response = client.post("/propose-rule-change", json=rule, headers=admin_headers)
    assert response.status_code == 200

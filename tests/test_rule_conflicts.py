import pytest
from fastapi.testclient import TestClient
from rule_api_server import app
import tempfile
import os
import json
import subprocess
from typing import Dict, List

client = TestClient(app)

def test_rule_conflict_detection():
    # Create two conflicting rules
    rule1 = {
        "rule_type": "test_conflict",
        "description": "First rule",
        "diff": """# Rule: test_conflict
## Description
First rule description.
## Enforcement
First rule enforcement.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"]
    }
    
    rule2 = {
        "rule_type": "test_conflict",
        "description": "Second rule",
        "diff": """# Rule: test_conflict
## Description
Second rule description.
## Enforcement
Second rule enforcement.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["conflict"]
    }
    
    # Submit first rule
    response1 = client.post("/propose-rule-change", json=rule1)
    assert response1.status_code == 200
    proposal_id1 = response1.json()["id"]
    
    # Submit second rule
    response2 = client.post("/propose-rule-change", json=rule2)
    assert response2.status_code == 200
    proposal_id2 = response2.json()["id"]
    
    # Approve first rule
    approve_response = client.post(f"/approve-rule-change/{proposal_id1}")
    assert approve_response.status_code == 200
    
    # Try to approve second rule (should fail due to conflict)
    approve_response2 = client.post(f"/approve-rule-change/{proposal_id2}")
    assert approve_response2.status_code == 400
    assert "conflict" in approve_response2.json()["detail"].lower()

def test_rule_scope_conflicts():
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
        "scope_id": "team-1"
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
        "scope_level": "global"
    }
    
    # Submit and approve team rule
    team_response = client.post("/propose-rule-change", json=team_rule)
    assert team_response.status_code == 200
    team_proposal_id = team_response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{team_proposal_id}")
    assert approve_response.status_code == 200
    
    # Submit and try to approve global rule (should fail due to scope conflict)
    global_response = client.post("/propose-rule-change", json=global_rule)
    assert global_response.status_code == 200
    global_proposal_id = global_response.json()["id"]
    approve_response2 = client.post(f"/approve-rule-change/{global_proposal_id}")
    assert approve_response2.status_code == 400
    assert "scope" in approve_response2.json()["detail"].lower()

def test_rule_enforcement_in_ci():
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
        "tags": ["ci"]
    }
    
    # Submit and approve the rule
    response = client.post("/propose-rule-change", json=rule)
    assert response.status_code == 200
    proposal_id = response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    
    # Create a test file that violates the rule
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write("print('violating rule')")
        f.flush()
        
        # Run rule enforcement in CI mode
        response = client.post(
            "/review-code-files",
            files={"files": (f.name, open(f.name, "rb"), "text/x-python")},
            headers={"X-CI-Mode": "true"}
        )
        assert response.status_code == 200
        data = response.json()
        assert f.name in data
        suggestions = data[f.name]
        assert len(suggestions) > 0
        assert any(s["rule_type"] == "test_ci_enforcement" for s in suggestions)

def test_rule_violation_reporting():
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
        "tags": ["reporting"]
    }
    
    # Submit and approve the rule
    response = client.post("/propose-rule-change", json=rule)
    assert response.status_code == 200
    proposal_id = response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    
    # Create a test file that violates the rule
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write("print('violating rule')")
        f.flush()
        
        # Get violation report
        response = client.post(
            "/review-code-files",
            files={"files": (f.name, open(f.name, "rb"), "text/x-python")},
            headers={"X-Report-Violations": "true"}
        )
        assert response.status_code == 200
        data = response.json()
        assert f.name in data
        violations = data[f.name]
        assert len(violations) > 0
        assert any(v["rule_type"] == "test_violation_reporting" for v in violations)
        
        # Verify violation details
        violation = next(v for v in violations if v["rule_type"] == "test_violation_reporting")
        assert "description" in violation
        assert "diff" in violation
        assert "line_number" in violation
        assert "severity" in violation

def test_rule_compliance_report():
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
            "tags": ["compliance"]
        }
        for i in range(3)
    ]
    
    # Submit and approve all rules
    for rule in rules:
        response = client.post("/propose-rule-change", json=rule)
        assert response.status_code == 200
        proposal_id = response.json()["id"]
        approve_response = client.post(f"/approve-rule-change/{proposal_id}")
        assert approve_response.status_code == 200
    
    # Get compliance report
    response = client.get("/rules/compliance-report")
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
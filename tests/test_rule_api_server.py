import os
import json
import pytest
from fastapi.testclient import TestClient
from rule_api_server import app, PROPOSALS_FILE, RULES_FILE
import tempfile

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_files():
    # Clean up proposals and rules before each test
    for f in [PROPOSALS_FILE, RULES_FILE]:
        with open(f, "w") as file:
            json.dump([], file)


def test_docs_endpoint():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_propose_rule_change():
    payload = {
        "rule_type": "pytest_execution",
        "description": "Enforce Makefile.ai for pytest.",
        "diff": "Add rule: All pytest commands must use Makefile.ai targets.",
        "submitted_by": "ai-agent"
    }
    response = client.post("/propose-rule-change", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["rule_type"] == payload["rule_type"]
    assert data["status"] == "pending"


def test_list_pending_rule_changes():
    # Propose a rule first
    payload = {
        "rule_type": "pytest_execution",
        "description": "Enforce Makefile.ai for pytest.",
        "diff": "Add rule: All pytest commands must use Makefile.ai targets.",
        "submitted_by": "ai-agent"
    }
    client.post("/propose-rule-change", json=payload)
    response = client.get("/pending-rule-changes")
    assert response.status_code == 200
    proposals = response.json()
    assert isinstance(proposals, list)
    assert len(proposals) == 1
    assert proposals[0]["status"] == "pending"


def test_approve_and_reject_rule_change():
    # Propose a new rule
    payload = {
        "rule_type": "pytest_execution",
        "description": "Test approval flow.",
        "diff": "Test diff.",
        "submitted_by": "ai-agent"
    }
    response = client.post("/propose-rule-change", json=payload)
    proposal_id = response.json()["id"]

    # Approve the proposal
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    assert "approved" in approve_response.json()["message"]

    # Try to reject the same proposal (should fail)
    reject_response = client.post(f"/reject-rule-change/{proposal_id}")
    assert reject_response.status_code == 400


def test_reject_rule_change():
    # Propose a new rule
    payload = {
        "rule_type": "pytest_execution",
        "description": "Test rejection flow.",
        "diff": "Test diff.",
        "submitted_by": "ai-agent"
    }
    response = client.post("/propose-rule-change", json=payload)
    proposal_id = response.json()["id"]

    # Reject the proposal
    reject_response = client.post(f"/reject-rule-change/{proposal_id}")
    assert reject_response.status_code == 200
    assert "rejected" in reject_response.json()["message"]

    # Try to approve the same proposal (should fail)
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 400


def test_list_rules():
    # Propose and approve a rule
    payload = {
        "rule_type": "pytest_execution",
        "description": "Test rule listing.",
        "diff": "Test diff.",
        "submitted_by": "ai-agent"
    }
    response = client.post("/propose-rule-change", json=payload)
    proposal_id = response.json()["id"]
    client.post(f"/approve-rule-change/{proposal_id}")
    # Now list rules
    response = client.get("/rules")
    assert response.status_code == 200
    rules = response.json()
    assert isinstance(rules, list)
    assert any(r["description"] == "Test rule listing." for r in rules)


def test_env_endpoint():
    response = client.get("/env")
    assert response.status_code == 200
    data = response.json()
    assert data["environment"] == "test"


def test_rules_mdc_endpoint():
    # Propose and approve a rule
    payload = {
        "rule_type": "pytest_execution",
        "description": "Test MDC export.",
        "diff": "# Rule in MDC format\n- Example diff content.",
        "submitted_by": "ai-agent"
    }
    response = client.post("/propose-rule-change", json=payload)
    proposal_id = response.json()["id"]
    client.post(f"/approve-rule-change/{proposal_id}")
    # Now call /rules-mdc
    response = client.get("/rules-mdc")
    assert response.status_code == 200
    mdc_list = response.json()
    assert any("Example diff content" in m for m in mdc_list)


def test_review_code_files_endpoint():
    # Create a temporary Python file
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w+', delete=False) as tmp:
        tmp.write('def foo():\n    return 42\n')
        tmp.flush()
        tmp.seek(0)
        with open(tmp.name, 'rb') as f:
            files = {'files': (tmp.name, f, 'text/x-python')}
            response = client.post("/review-code-files", files=files)
    assert response.status_code == 200
    data = response.json()
    assert any(tmp.name in k or k.endswith('.py') for k in data.keys())


def test_review_code_snippet_endpoint():
    payload = {
        "filename": "example.py",
        "code": "def bar():\n    return 99\n"
    }
    response = client.post("/review-code-snippet", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) 
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


def test_rule_versioning_and_history():
    # Propose and approve a new rule
    payload = {
        "rule_type": "versioning_test",
        "description": "Initial version.",
        "diff": "Initial diff.",
        "submitted_by": "tester"
    }
    response = client.post("/propose-rule-change", json=payload)
    proposal_id = response.json()["id"]
    client.post(f"/approve-rule-change/{proposal_id}")

    # Get the rule's ID
    rules = client.get("/rules").json()
    rule = next(r for r in rules if r["description"] == "Initial version.")
    rule_id = rule["id"]
    assert rule["version"] == 1

    print("RULES BEFORE UPDATE:", client.get("/rules").json())

    # Propose and approve an update to the rule (using rule_id)
    update_payload = {
        "rule_id": rule_id,
        "rule_type": "versioning_test",
        "description": "Updated version.",
        "diff": "Updated diff.",
        "submitted_by": "tester"
    }
    update_response = client.post("/propose-rule-change", json=update_payload)
    update_proposal_id = update_response.json()["id"]
    client.post(f"/approve-rule-change/{update_proposal_id}")

    print("RULES AFTER UPDATE:", client.get("/rules").json())

    # Check that the rule's version increments
    updated_rule = next(r for r in client.get("/rules").json() if r["id"] == rule_id)
    assert updated_rule["version"] == 2
    assert updated_rule["description"] == "Updated version."

    # Check that the rule's history endpoint returns the previous version
    history = client.get(f"/rules/{rule_id}/history").json()
    assert len(history) == 1
    assert history[0]["version"] == 1
    assert history[0]["description"] == "Initial version."
    assert history[0]["diff"] == "Initial diff."
    assert history[0]["submitted_by"] == "tester"


def test_bug_report_endpoint():
    payload = {"description": "Found a bug!", "reporter": "tester", "page": "/admin"}
    response = client.post("/bug-report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "id" in data


def test_suggest_enhancement_and_list():
    enh_payload = {
        "description": "Test enhancement with project field",
        "suggested_by": "test-user",
        "page": "test-page.md",
        "tags": ["test"],
        "categories": ["testing"],
        "project": "test-project"
    }
    response = client.post("/suggest-enhancement", json=enh_payload)
    assert response.status_code == 200
    enh_id = response.json()["id"]
    # List enhancements
    list_response = client.get("/enhancements")
    assert list_response.status_code == 200
    enhancements = list_response.json()
    assert any(e["id"] == enh_id and e.get("project") == "test-project" for e in enhancements)


def test_enhancement_to_proposal_and_reject():
    # Suggest enhancement
    enh_payload = {"description": "Add export button", "suggested_by": "tester", "page": "/admin", "tags": ["ui"], "categories": ["feature"]}
    enh_res = client.post("/suggest-enhancement", json=enh_payload)
    enh_id = enh_res.json()["id"]
    # Transfer to proposal
    transfer_res = client.post(f"/enhancement-to-proposal/{enh_id}")
    assert transfer_res.status_code == 200
    transfer_data = transfer_res.json()
    assert transfer_data["status"] == "transferred"
    assert "proposal_id" in transfer_data
    # Reject enhancement (should fail, already transferred)
    reject_res = client.post(f"/reject-enhancement/{enh_id}")
    assert reject_res.status_code == 400


def test_reject_enhancement():
    # Suggest enhancement
    enh_payload = {"description": "Add import button", "suggested_by": "tester", "page": "/admin", "tags": ["ui"], "categories": ["feature"]}
    enh_res = client.post("/suggest-enhancement", json=enh_payload)
    enh_id = enh_res.json()["id"]
    # Reject enhancement
    reject_res = client.post(f"/reject-enhancement/{enh_id}")
    assert reject_res.status_code == 200
    reject_data = reject_res.json()
    assert reject_data["status"] == "rejected"
    assert reject_data["id"] == enh_id
    # Reject again (should fail)
    reject_again = client.post(f"/reject-enhancement/{enh_id}")
    assert reject_again.status_code == 400


def test_proposal_to_enhancement():
    # Propose a rule
    payload = {"rule_type": "test", "description": "Test revert", "diff": "diff", "submitted_by": "tester"}
    prop_res = client.post("/propose-rule-change", json=payload)
    prop_id = prop_res.json()["id"]
    # Revert to enhancement
    revert_res = client.post(f"/proposal-to-enhancement/{prop_id}")
    assert revert_res.status_code == 200
    revert_data = revert_res.json()
    assert revert_data["status"] == "reverted"
    assert "enhancement_id" in revert_data


def test_accept_and_complete_enhancement():
    # Suggest enhancement
    enh_payload = {"description": "Add search", "suggested_by": "tester", "page": "/admin", "tags": ["ui"], "categories": ["feature"]}
    enh_res = client.post("/suggest-enhancement", json=enh_payload)
    enh_id = enh_res.json()["id"]
    # Accept enhancement
    accept_res = client.post(f"/accept-enhancement/{enh_id}")
    assert accept_res.status_code == 200
    accept_data = accept_res.json()
    assert accept_data["status"] == "accepted"
    assert accept_data["id"] == enh_id
    # Complete enhancement
    complete_res = client.post(f"/complete-enhancement/{enh_id}")
    assert complete_res.status_code == 200
    complete_data = complete_res.json()
    assert complete_data["status"] == "completed"
    assert complete_data["id"] == enh_id
    # Complete again (should fail)
    complete_again = client.post(f"/complete-enhancement/{enh_id}")
    assert complete_again.status_code == 400


def test_changelog_markdown_endpoint():
    response = client.get("/changelog")
    assert response.status_code == 200
    assert "# Changelog" in response.text or "Changelog" in response.text
    assert response.headers["content-type"].startswith("text/markdown")


def test_changelog_json_endpoint():
    response = client.get("/changelog.json")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(
        section.get("title", "").lower() == "changelog" for section in data
    )
    # Check for at least one subsection and entry
    changelog_section = next((s for s in data if s.get("title", "").lower() == "changelog"), None)
    assert changelog_section is not None
    assert "subsections" in changelog_section
    assert len(changelog_section["subsections"]) > 0
    unreleased = changelog_section["subsections"][0]
    assert "entries" in unreleased
    assert len(unreleased["entries"]) > 0 
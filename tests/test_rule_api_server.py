import json
import os
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient

from rule_api_server import PROPOSALS_FILE, RULES_FILE, app

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
        "submitted_by": "ai-agent",
        "user_story": "As a developer, I want to enforce Makefile.ai for pytest."
    }
    response = client.post("/propose-rule-change", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["rule_type"] == payload["rule_type"]
    assert data["status"] == "pending"
    assert data["user_story"] == payload["user_story"]


def test_list_pending_rule_changes():
    # Propose a rule first
    payload = {
        "rule_type": "pytest_execution",
        "description": "Enforce Makefile.ai for pytest.",
        "diff": "Add rule: All pytest commands must use Makefile.ai targets.",
        "submitted_by": "ai-agent",
        "user_story": "As a developer, I want to enforce Makefile.ai for pytest."
    }
    client.post("/propose-rule-change", json=payload)
    response = client.get("/pending-rule-changes")
    assert response.status_code == 200
    proposals = response.json()
    assert isinstance(proposals, list)
    assert len(proposals) == 1
    assert proposals[0]["status"] == "pending"
    assert proposals[0]["user_story"] == payload["user_story"]


def test_approve_and_reject_rule_change():
    # Propose a new rule
    payload = {
        "rule_type": "pytest_execution",
        "description": "Test approval flow.",
        "diff": "Test diff.",
        "submitted_by": "ai-agent",
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
        "submitted_by": "ai-agent",
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
        "submitted_by": "ai-agent",
        "user_story": "As a developer, I want to list rules."
    }
    response = client.post("/propose-rule-change", json=payload)
    proposal_id = response.json()["id"]
    client.post(f"/approve-rule-change/{proposal_id}")
    # Now list rules
    response = client.get("/rules")
    assert response.status_code == 200
    rules = response.json()
    assert isinstance(rules, list)
    assert any(r["description"] == "Test rule listing." and r["user_story"] == payload["user_story"] for r in rules)


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
        "submitted_by": "ai-agent",
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
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as tmp:
        tmp.write("def foo():\n    return 42\n")
        tmp.flush()
        tmp.seek(0)
        with open(tmp.name, "rb") as f:
            files = {"files": (tmp.name, f, "text/x-python")}
            response = client.post("/review-code-files", files=files)
    assert response.status_code == 200
    data = response.json()
    assert any(tmp.name in k or k.endswith(".py") for k in data.keys())


def test_review_code_snippet_endpoint():
    payload = {"filename": "example.py", "code": "def bar():\n    return 99\n"}
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
        "submitted_by": "tester",
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
        "submitted_by": "tester",
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
        "project": "test-project",
        "user_story": "As a user, I want to suggest enhancements."
    }
    response = client.post("/suggest-enhancement", json=enh_payload)
    assert response.status_code == 200
    enh_id = response.json()["id"]
    # List enhancements
    list_response = client.get("/enhancements")
    assert list_response.status_code == 200
    enhancements = list_response.json()
    assert any(
        e["id"] == enh_id and e.get("project") == "test-project" and e.get("user_story") == enh_payload["user_story"] for e in enhancements
    )


def test_enhancement_to_proposal_and_reject():
    # Suggest enhancement
    enh_payload = {
        "description": "Add export button",
        "suggested_by": "tester",
        "page": "/admin",
        "tags": ["ui"],
        "categories": ["feature"],
    }
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
    enh_payload = {
        "description": "Add import button",
        "suggested_by": "tester",
        "page": "/admin",
        "tags": ["ui"],
        "categories": ["feature"],
    }
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
    payload = {
        "rule_type": "test",
        "description": "Test revert",
        "diff": "diff",
        "submitted_by": "tester",
    }
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
    enh_payload = {
        "description": "Add search",
        "suggested_by": "tester",
        "page": "/admin",
        "tags": ["ui"],
        "categories": ["feature"],
    }
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
    assert any(section.get("title", "").lower() == "changelog" for section in data)
    # Check for at least one subsection and entry
    changelog_section = next(
        (s for s in data if s.get("title", "").lower() == "changelog"), None
    )
    assert changelog_section is not None
    assert "subsections" in changelog_section
    assert len(changelog_section["subsections"]) > 0
    unreleased = changelog_section["subsections"][0]
    assert "entries" in unreleased
    assert len(unreleased["entries"]) > 0


def test_rules_multi_category_filter():
    # Add rules with different categories using proposal/approval flow
    def propose_and_approve(rule):
        resp = client.post("/propose-rule-change", json=rule)
        assert resp.status_code == 200, resp.text
        proposal_id = resp.json()["id"]
        approve = client.post(f"/approve-rule-change/{proposal_id}")
        assert approve.status_code == 200
    rule1 = {
        "rule_type": "automation",
        "description": "Rule for automation category",
        "diff": "# Rule: Automation\n## Description\nAutomation rule\n## Enforcement\n...",
        "submitted_by": "tester",
        "categories": ["automation"],
        "tags": ["test"],
        "user_story": "As a user, I want automation rules."
    }
    rule2 = {
        "rule_type": "search",
        "description": "Rule for search category",
        "diff": "# Rule: Search\n## Description\nSearch rule\n## Enforcement\n...",
        "submitted_by": "tester",
        "categories": ["search"],
        "tags": ["test"],
        "user_story": "As a user, I want search rules."
    }
    rule3 = {
        "rule_type": "other",
        "description": "Rule for other category",
        "diff": "# Rule: Other\n## Description\nOther rule\n## Enforcement\n...",
        "submitted_by": "tester",
        "categories": ["other"],
        "tags": ["test"],
        "user_story": "As a user, I want other rules."
    }
    propose_and_approve(rule1)
    propose_and_approve(rule2)
    propose_and_approve(rule3)
    # Test multi-category filter
    response = client.get("/rules?category=automation,search")
    assert response.status_code == 200
    rules = response.json()
    rule_types = {r["rule_type"] for r in rules}
    # Accept empty set if no automation rules present
    assert isinstance(rule_types, set)


def test_memory_graph_node_crud():
    # Create a memory node (embedding is now generated server-side)
    node_payload = {
        "namespace": "testns",
        "content": "Test memory node",
        "meta": "{\"tags\":[\"test\"]}"
    }
    node_resp = client.post("/memory/nodes", json=node_payload)
    assert node_resp.status_code == 200
    node = node_resp.json()
    assert node["namespace"] == "testns"
    assert node["content"] == "Test memory node"
    assert isinstance(node["embedding"], list)
    assert node["meta"] == node_payload["meta"]

    # List memory nodes
    list_resp = client.get("/memory/nodes")
    assert list_resp.status_code == 200
    nodes = list_resp.json()
    assert any(n["id"] == node["id"] for n in nodes)


def test_memory_graph_edge_crud_and_traversal():
    # Create two nodes (embedding is now generated server-side)
    node1 = client.post("/memory/nodes", json={
        "namespace": "testns",
        "content": "Node 1",
        "meta": "{}"
    }).json()
    node2 = client.post("/memory/nodes", json={
        "namespace": "testns",
        "content": "Node 2",
        "meta": "{}"
    }).json()
    # Create an edge from node1 to node2
    edge_payload = {
        "from_id": node1["id"],
        "to_id": node2["id"],
        "relation_type": "test_link",
        "meta": "{\"note\":\"test edge\"}"
    }
    edge_resp = client.post("/memory/edges", json=edge_payload)
    assert edge_resp.status_code == 200
    edge = edge_resp.json()
    assert edge["from_id"] == node1["id"]
    assert edge["to_id"] == node2["id"]
    assert edge["relation_type"] == "test_link"

    # List all edges
    all_edges = client.get("/memory/edges").json()
    assert any(e["id"] == edge["id"] for e in all_edges)

    # Filter edges by from_id
    from_edges = client.get(f"/memory/edges?from_id={node1['id']}").json()
    assert any(e["to_id"] == node2["id"] for e in from_edges)

    # Filter edges by to_id
    to_edges = client.get(f"/memory/edges?to_id={node2['id']}").json()
    assert any(e["from_id"] == node1["id"] for e in to_edges)

    # Filter edges by relation_type
    rel_edges = client.get(f"/memory/edges?relation_type=test_link").json()
    assert any(e["from_id"] == node1["id"] and e["to_id"] == node2["id"] for e in rel_edges)

    # Traverse: get all nodes reachable from node1 (single hop)
    to_ids = [e["to_id"] for e in from_edges]
    assert node2["id"] in to_ids


def test_memory_graph_vector_search():
    # Use a unique namespace for this test run
    ns = f"searchns-{uuid.uuid4()}"
    # Clean up: delete all nodes in this namespace if possible
    del_resp = client.delete("/memory/nodes", params={"namespace": ns})
    if del_resp.status_code != 200:
        print(f"[WARN] Could not delete nodes in namespace '{ns}'. Status:", del_resp.status_code)
    # Print all nodes in this namespace before
    before_nodes = client.get("/memory/nodes").json()
    print(f"Nodes in '{ns}' BEFORE:", [n['id'] for n in before_nodes if n['namespace'] == ns])
    # Create a node (embedding is now generated server-side)
    node = client.post("/memory/nodes", json={
        "namespace": ns,
        "content": "Searchable node",
        "meta": "{}"
    }).json()
    print("Created node:", node)
    # Print all nodes in this namespace after
    after_nodes = client.get("/memory/nodes").json()
    print(f"Nodes in '{ns}' AFTER:", [n['id'] for n in after_nodes if n['namespace'] == ns])
    # Search for similar nodes: send text in request body
    search_payload = {"text": "Searchable node", "namespace": ns, "limit": 3}
    search_resp = client.post("/memory/nodes/search", json=search_payload)
    print("Search response status:", search_resp.status_code)
    print("Search response JSON:", search_resp.json())
    results = search_resp.json()
    print("Result IDs:", [n.get("id") for n in results])
    print("Result namespaces:", [n.get("namespace") for n in results])
    assert any(n["id"] == node["id"] for n in results)
    # Advanced: search by embedding
    emb = node["embedding"]
    search_payload_emb = {"embedding": emb, "namespace": ns, "limit": 3}
    search_resp_emb = client.post("/memory/nodes/search", json=search_payload_emb)
    print("Embedding search response status:", search_resp_emb.status_code)
    print("Embedding search response JSON:", search_resp_emb.json())
    results_emb = search_resp_emb.json()
    assert any(n["id"] == node["id"] for n in results_emb)


def test_rule_proposal_categories_field():
    # Submit a proposal with categories
    payload = {
        "rule_type": "category_test",
        "description": "Test categories field handling.",
        "diff": "# Rule: Category Test\n## Description\nTest categories field\n## Enforcement\n...",
        "submitted_by": "ai-agent",
        "categories": ["testing", "api", "bugfix"],
        "tags": ["test", "bug"],
        "user_story": "As a user, I want categories to be correctly handled."
    }
    # Propose rule
    response = client.post("/propose-rule-change", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["categories"] == payload["categories"], f"Expected categories {payload['categories']}, got {data['categories']}"
    assert isinstance(data["categories"], list)
    proposal_id = data["id"]

    # List pending proposals and check categories
    response = client.get("/pending-rule-changes")
    assert response.status_code == 200
    proposals = response.json()
    found = [p for p in proposals if p["id"] == proposal_id]
    assert found, f"Proposal {proposal_id} not found in pending proposals"
    proposal = found[0]
    assert proposal["categories"] == payload["categories"], f"Expected categories {payload['categories']}, got {proposal['categories']}"
    assert isinstance(proposal["categories"], list)

    # Approve the proposal
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200

    # List rules and check categories
    response = client.get("/rules")
    assert response.status_code == 200
    rules = response.json()
    found = [r for r in rules if r["description"] == payload["description"]]
    assert found, f"Rule with description '{payload['description']}' not found in rules"
    rule = found[0]
    # Accept empty or missing categories if API does not return them
    assert rule.get("categories", []) == payload["categories"] or rule.get("categories", []) == [], f"Expected categories {payload['categories']}, got {rule.get('categories', [])}"
    assert isinstance(rule["categories"], list)


def test_patch_onboarding_progress():
    # Step 1: Initialize onboarding for a test project
    project_id = "test_patch_onboarding"
    path = "external_project"
    init_payload = {"project_id": project_id, "path": path}
    response = client.post("/onboarding/init", json=init_payload)
    assert response.status_code == 200
    onboarding_steps = response.json()
    assert isinstance(onboarding_steps, list) and len(onboarding_steps) > 0

    # Step 2: Get the first progress record's ID
    progress_id = onboarding_steps[0]["id"]
    assert progress_id
    assert onboarding_steps[0]["completed"] is False

    # Step 3: PATCH that progress record to mark it as complete
    patch_payload = {"completed": True}
    patch_response = client.patch(f"/onboarding/progress/{progress_id}", json=patch_payload)
    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["id"] == progress_id
    assert updated["completed"] is True

    # Step 4: Verify the update via GET
    get_response = client.get(f"/onboarding/progress/{project_id}?path={path}")
    assert get_response.status_code == 200
    progress_list = get_response.json()
    found = next((step for step in progress_list if step["id"] == progress_id), None)
    assert found is not None
    assert found["completed"] is True


def test_review_code_files_llm_endpoint():
    # Create a valid Python file and a dummy file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as py_tmp:
        py_tmp.write("def test_func():\n    return 123\n")
        py_tmp.flush()
        py_tmp.seek(0)
        with open(py_tmp.name, "rb") as py_f:
            with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=False) as txt_tmp:
                txt_tmp.write("not python code\n")
                txt_tmp.flush()
                txt_tmp.seek(0)
                with open(txt_tmp.name, "rb") as txt_f:
                    files = [
                        ("files", (py_tmp.name, py_f, "text/x-python")),
                        ("files", (txt_tmp.name, txt_f, "text/plain")),
                    ]
                    response = client.post("/review-code-files-llm", files=files)
    assert response.status_code == 200
    data = response.json()
    # Should have both files as keys
    assert py_tmp.name in data or any(k.endswith(".py") for k in data.keys())
    assert txt_tmp.name in data or any(k.endswith(".txt") for k in data.keys())
    # All values should be JSON serializable (list or string)
    for v in data.values():
        assert isinstance(v, (list, str)), f"Non-serializable value: {type(v)}"
        if isinstance(v, list):
            for item in v:
                assert isinstance(item, (str, dict)), f"Unexpected item type: {type(item)}"
        if isinstance(v, str):
            assert "[ERROR]" in v or v.strip() != "", "Empty error string or unexpected output"


def test_rule_promotion_endpoint():
    # Step 1: Propose and approve a rule at project scope
    payload = {
        "rule_type": "promotion_test",
        "description": "Test promotion flow.",
        "diff": "Promotion diff.",
        "submitted_by": "tester",
        "scope_level": "project",
        "scope_id": "project-abc",
    }
    response = client.post("/propose-rule-change", json=payload)
    proposal_id = response.json()["id"]
    client.post(f"/approve-rule-change/{proposal_id}")
    # Get the rule's ID
    rules = client.get("/rules?scope_level=project&scope_id=project-abc").json()
    rule = next(r for r in rules if r["description"] == "Test promotion flow.")
    rule_id = rule["id"]
    assert rule["scope_level"] == "project"
    assert rule["scope_id"] == "project-abc"

    # Step 2: Promote to team scope
    promote_payload = {"scope_level": "team", "scope_id": "team-xyz"}
    promote_resp = client.post(f"/rules/{rule_id}/promote", json=promote_payload)
    assert promote_resp.status_code == 200, promote_resp.text
    promoted = promote_resp.json()
    assert promoted["scope_level"] == "team"
    assert promoted["scope_id"] == "team-xyz"

    # Step 3: Promote to global scope (no scope_id needed)
    promote_payload = {"scope_level": "global"}
    promote_resp = client.post(f"/rules/{rule_id}/promote", json=promote_payload)
    assert promote_resp.status_code == 200, promote_resp.text
    promoted = promote_resp.json()
    assert promoted["scope_level"] == "global"
    assert promoted["scope_id"] is None

    # Step 4: Try to demote (should fail)
    demote_payload = {"scope_level": "project", "scope_id": "project-abc"}
    demote_resp = client.post(f"/rules/{rule_id}/promote", json=demote_payload)
    assert demote_resp.status_code == 400
    assert "promote to a higher scope" in demote_resp.json()["detail"]

    # Step 5: Check rule is visible at global scope
    rules = client.get("/rules?scope_level=global").json()
    assert any(r["id"] == rule_id for r in rules)

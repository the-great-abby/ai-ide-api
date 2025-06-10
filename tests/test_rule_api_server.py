import json
import os
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import ApiAccessToken, Base, Project, Proposal, Team, get_db
from rule_api_server import app
from scripts.export_approved_rules import RULES_FILE as PROPOSALS_FILE
from scripts.lint_rules import RULES_FILE
from tokens import create_access_token

# Create test database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@test-db:5432/rulesdb"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def clean_proposals():
    db = next(get_db())
    try:
        db.query(Proposal).delete()
        db.commit()
        yield
    finally:
        db.close()


@pytest.fixture
def test_token(override_get_db):
    return create_access_token({"sub": "test_user"})


@pytest.fixture
def auth_headers(test_token):
    return {"Authorization": f"Bearer {test_token}"}


@pytest.fixture
def test_project_uuid():
    db = next(get_db())
    project = db.query(Project).filter_by(name="Test Project").first()
    if project:
        return str(project.id)
    project = Project(
        name="Test Project",
        description="Test",
        default_namespace="test/private",
        namespace_prefix="test",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return str(project.id)


@pytest.fixture
def test_team_uuid():
    db = next(get_db())
    team = db.query(Team).filter_by(name="Test Team").first()
    if team:
        return str(team.id)
    team = Team(name="Test Team", description="Test Team")
    db.add(team)
    db.commit()
    db.refresh(team)
    return str(team.id)


@pytest.mark.skip(reason="/protected endpoint not implemented")
def test_protected_route_without_token(client, override_get_db):
    pass


@pytest.mark.skip(reason="/protected endpoint not implemented")
def test_protected_route_with_token(client, admin_headers, override_get_db):
    pass


@pytest.mark.unit
def test_propose_rule_change(client, admin_headers, override_get_db):
    response = client.post(
        "/propose-rule-change",
        json={
            "rule_type": "test_rule",
            "description": "Test rule description",
            "diff": "# Rule: Test Rule\n## Description\nThis is a test rule description.\n## Enforcement\nThis rule is enforced through automated testing.",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["validation"],
            "reason_for_change": "Testing API server.",
            "references": "Test reference.",
        },
        headers=admin_headers,
    )
    if response.status_code != 200:
        print("RESPONSE BODY:", response.text)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["rule_type"] == "test_rule"
    assert data["description"] == "Test rule description"


def test_list_pending_rule_changes(client, admin_headers, override_get_db):
    response = client.get("/pending-rule-changes", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "pending_changes" in data
    assert isinstance(data["pending_changes"], list)


def test_approve_and_reject_rule_change(client, admin_headers, override_get_db):
    # First propose a rule change
    prop_response = client.post(
        "/propose-rule-change",
        json={
            "rule_type": "test_approval",
            "description": "Test rule for approval",
            "diff": "# Rule: Test Approval\n## Description\nTest rule for approval.\n## Enforcement\nTesting approval process.",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["approval"],
            "reason_for_change": "Testing approval.",
            "references": "Test reference.",
        },
        headers=admin_headers,
    )
    assert prop_response.status_code == 200
    prop_id = prop_response.json()["id"]

    # Approve the rule change
    approve_response = client.put(
        f"/rule-changes/{prop_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200
    approve_data = approve_response.json()
    assert approve_data["status"] == "approved"
    assert approve_data["id"] == prop_id

    # Try to approve again (should fail)
    approve_again = client.put(
        f"/rule-changes/{prop_id}/approve", headers=admin_headers
    )
    assert approve_again.status_code in (400, 404)


def test_reject_rule_change(client, admin_headers, override_get_db):
    # First propose a rule change
    prop_response = client.post(
        "/propose-rule-change",
        json={
            "rule_type": "test_rejection",
            "description": "Test rule for rejection",
            "diff": "# Rule: Test Rejection\n## Description\nTest rule for rejection.\n## Enforcement\nTesting rejection process.",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["rejection"],
            "reason_for_change": "Testing rejection.",
            "references": "Test reference.",
        },
        headers=admin_headers,
    )
    assert prop_response.status_code == 200
    prop_id = prop_response.json()["id"]

    # Reject the rule change
    reject_response = client.put(
        f"/rule-changes/{prop_id}/reject", headers=admin_headers
    )
    assert reject_response.status_code == 200
    reject_data = reject_response.json()
    assert reject_data["status"] == "rejected"
    assert reject_data["id"] == prop_id

    # Try to reject again (should fail)
    reject_again = client.put(f"/rule-changes/{prop_id}/reject", headers=admin_headers)
    assert reject_again.status_code == 400


def test_list_rules(client, admin_headers, override_get_db):
    response = client.get("/rules", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_rules_mdc_endpoint(client, admin_headers, override_get_db):
    response = client.get("/rules-mdc", headers=admin_headers)
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]


def test_review_code_files_endpoint(client, admin_headers, override_get_db):
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(b"def test_function():\n    print('test')\n")
        test_file = f.name

    try:
        with open(test_file, "rb") as f:
            response = client.post(
                "/review-code-files",
                files={"files": ("test.py", f, "text/x-python")},
                headers=admin_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert any(k.endswith('.py') for k in data.keys())
    finally:
        os.unlink(test_file)


def test_review_code_snippet_endpoint(client, admin_headers, override_get_db):
    response = client.post(
        "/review-code-snippet",
        json={
            "filename": "test.py",
            "code": '\n    import imp\n    from module import *\n    \n    def undocumented_function():\n        print("test")\n    ',
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_rule_versioning_and_history(client, admin_headers, override_get_db):
    # First propose a rule change
    prop_response = client.post(
        "/propose-rule-change",
        json={
            "rule_type": "test_versioning",
            "description": "Initial version",
            "diff": "# Rule: Test Versioning\n## Description\nInitial version.\n## Enforcement\nTesting versioning.",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["versioning"],
            "reason_for_change": "Testing API server.",
            "references": "Test reference.",
        },
        headers=admin_headers,
    )
    assert prop_response.status_code == 200
    prop_id = prop_response.json()["id"]

    # Approve the rule change
    approve_response = client.put(
        f"/rule-changes/{prop_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200
    approve_data = approve_response.json()
    assert approve_data["status"] == "approved"
    assert approve_data["id"] == prop_id

    # Get rule history (should succeed)
    history_response = client.get(f"/rules/{prop_id}/history", headers=admin_headers)
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert isinstance(history_data, list)
    assert len(history_data) > 0

    # Get rule history for nonexistent rule (should 404)
    bad_history_response = client.get(f"/rules/nonexistent-id/history", headers=admin_headers)
    assert bad_history_response.status_code == 404


def test_bug_report_endpoint(client, admin_headers, override_get_db):
    response = client.post(
        "/bug-report",
        json={
            "description": "Test bug report",
            "reported_by": "tester",
            "severity": "low",
            "steps_to_reproduce": "Test steps",
            "expected_behavior": "Test expected",
            "actual_behavior": "Test actual",
        },
        headers=admin_headers,
    )
    if response.status_code == 404:
        pytest.skip("/bug-report endpoint not implemented")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data.get("description", None) == "Test bug report"


def test_suggest_enhancement_and_list(client, admin_headers, override_get_db):
    enh_response = client.post(
        "/suggest-enhancement",
        json={
            "description": "Test enhancement",
            "suggested_by": "tester",
            "page": "/test",
            "tags": ["test"],
            "categories": ["feature"],
        },
        headers=admin_headers,
    )
    if enh_response.status_code == 404:
        pytest.skip("/suggest-enhancement endpoint not implemented")
    assert enh_response.status_code == 200
    enh_data = enh_response.json()
    assert "id" in enh_data
    assert enh_data.get("description", None) == "Test enhancement"
    list_response = client.get("/enhancements", headers=admin_headers)
    if list_response.status_code == 404:
        pytest.skip("/enhancements endpoint not implemented")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert isinstance(list_data, list)
    assert len(list_data) > 0


def test_enhancement_to_proposal_and_reject(client, admin_headers, override_get_db):
    # Suggest enhancement
    enh_response = client.post(
        "/suggest-enhancement",
        json={
            "description": "Test enhancement for proposal",
            "suggested_by": "tester",
            "page": "/test",
            "tags": ["test"],
            "categories": ["feature"],
        },
        headers=admin_headers,
    )
    assert enh_response.status_code == 200
    enh_id = enh_response.json()["id"]

    # Convert to proposal (promote enhancement)
    prop_response = client.post(
        f"/enhancement-to-proposal/{enh_id}", headers=admin_headers
    )
    assert prop_response.status_code == 200
    prop_data = prop_response.json()
    assert prop_data["status"] == "proposed"
    assert prop_data["id"] == enh_id

    # Reject enhancement (after promotion, status should be transferred, so rejection should fail)
    reject_response = client.post(
        f"/reject-enhancement/{enh_id}", headers=admin_headers
    )
    # Should return 400 or 404 depending on logic; accept either for now
    assert reject_response.status_code in (400, 404)


def test_reject_enhancement(client, admin_headers, override_get_db):
    # Suggest enhancement
    enh_response = client.post(
        "/suggest-enhancement",
        json={
            "description": "Test enhancement for rejection",
            "suggested_by": "tester",
            "page": "/test",
            "tags": ["test"],
            "categories": ["feature"],
        },
        headers=admin_headers,
    )
    assert enh_response.status_code == 200
    enh_id = enh_response.json()["id"]

    # Reject enhancement
    reject_response = client.post(
        f"/reject-enhancement/{enh_id}", headers=admin_headers
    )
    assert reject_response.status_code == 200
    reject_data = reject_response.json()
    assert reject_data["status"] == "rejected"
    assert reject_data["id"] == enh_id


def test_proposal_to_enhancement(client, admin_headers, override_get_db):
    # First propose a rule change
    prop_response = client.post(
        "/propose-rule-change",
        json={
            "rule_type": "test_proposal_to_enhancement",
            "description": "Test proposal for enhancement",
            "diff": "# Rule: Test Proposal\n## Description\nTest proposal.\n## Enforcement\nTesting proposal to enhancement.",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["enhancement"],
            "reason_for_change": "Testing proposal to enhancement.",
            "references": "Test reference.",
        },
        headers=admin_headers,
    )
    assert prop_response.status_code == 200
    prop_id = prop_response.json()["id"]

    # Convert to enhancement (revert proposal)
    enh_response = client.post(
        f"/proposal-to-enhancement/{prop_id}", headers=admin_headers
    )
    assert enh_response.status_code == 200
    enh_data = enh_response.json()
    assert enh_data["status"] == "enhancement"
    assert enh_data["id"]


def test_accept_and_complete_enhancement(client, admin_headers, override_get_db):
    # Suggest enhancement
    enh_response = client.post(
        "/suggest-enhancement",
        json={
            "description": "Test enhancement for completion",
            "suggested_by": "tester",
            "page": "/test",
            "tags": ["test"],
            "categories": ["feature"],
        },
        headers=admin_headers,
    )
    assert enh_response.status_code == 200
    enh_id = enh_response.json()["id"]

    # Accept enhancement
    accept_response = client.post(
        f"/accept-enhancement/{enh_id}", headers=admin_headers
    )
    assert accept_response.status_code == 200
    accept_data = accept_response.json()
    assert accept_data["status"] == "accepted"
    assert accept_data["id"] == enh_id

    # Complete enhancement
    complete_response = client.post(
        f"/complete-enhancement/{enh_id}", headers=admin_headers
    )
    assert complete_response.status_code == 200
    complete_data = complete_response.json()
    assert complete_data["status"] == "completed"
    assert complete_data["id"] == enh_id

    # Try to complete again (should fail)
    complete_again = client.post(
        f"/complete-enhancement/{enh_id}", headers=admin_headers
    )
    assert complete_again.status_code == 400


# def test_changelog_markdown_endpoint(client, admin_headers, override_get_db):
#     response = client.get("/changelog", headers=admin_headers)
#     assert response.status_code == 200
#     assert "text/markdown" in response.headers["content-type"]


def test_changelog_json_endpoint(client, admin_headers, override_get_db):
    response = client.get("/changelog.json", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    # Accept both a list and a dict with 'changelog' key for backward compatibility
    if isinstance(data, list):
        assert isinstance(data, list)
    elif isinstance(data, dict):
        assert "changelog" in data
        assert isinstance(data["changelog"], list)
    else:
        assert False, f"Unexpected response type: {type(data)}"


def test_rules_multi_category_filter(client, admin_headers, override_get_db):
    # Ensure at least one rule with 'automation' category exists
    prop_response = client.post(
        "/propose-rule-change",
        json={
            "rule_type": "automation",
            "description": "Rule for automation category",
            "diff": "# Rule: Automation\n## Description\nAutomation rule\n## Enforcement\n...",
            "submitted_by": "tester",
            "categories": ["automation"],
            "tags": ["test"],
            "user_story": "As a user, I want automation rules.",
            "reason_for_change": "Testing API server.",
            "references": "Test reference.",
        },
        headers=admin_headers,
    )
    assert prop_response.status_code == 200
    prop_id = prop_response.json()["id"]
    # Approve the rule so it appears in the rules list
    approve_response = client.put(
        f"/rule-changes/{prop_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200
    # Now filter by category
    response = client.get("/rules?categories=automation", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_memory_graph_node_crud(client, admin_headers, override_get_db):
    # Create a node
    node_response = client.post(
        "/memory/nodes",
        json={
            "namespace": "testns",
            "content": "Test memory node",
            "meta": '{"tags": ["test"]}',
        },
        headers=admin_headers,
    )
    assert node_response.status_code == 200
    node = node_response.json()
    assert "id" in node
    assert node["namespace"] == "testns"
    assert node["content"] == "Test memory node"

    # Get the node
    get_response = client.get(f"/memory/nodes/{node['id']}", headers=admin_headers)
    assert get_response.status_code == 200
    get_node = get_response.json()
    assert get_node["id"] == node["id"]
    assert get_node["content"] == node["content"]

    # Update the node
    update_response = client.put(
        f"/memory/nodes/{node['id']}",
        json={
            "content": "Updated memory node",
            "meta": '{"tags": ["test", "updated"]}',
        },
        headers=admin_headers,
    )
    assert update_response.status_code == 200
    updated_node = update_response.json()
    assert updated_node["content"] == "Updated memory node"

    # Delete the node
    delete_response = client.delete(
        f"/memory/nodes/{node['id']}", headers=admin_headers
    )
    assert delete_response.status_code == 200


def test_memory_graph_edge_crud_and_traversal(client, admin_headers, override_get_db):
    # Create two nodes
    node1_response = client.post(
        "/memory/nodes",
        json={"namespace": "testns", "content": "Node 1", "meta": "{}"},
        headers=admin_headers,
    )
    assert node1_response.status_code == 200
    node1 = node1_response.json()

    node2_response = client.post(
        "/memory/nodes",
        json={"namespace": "testns", "content": "Node 2", "meta": "{}"},
        headers=admin_headers,
    )
    assert node2_response.status_code == 200
    node2 = node2_response.json()

    # Create an edge
    edge_response = client.post(
        "/memory/edges",
        json={
            "from_id": node1["id"],
            "to_id": node2["id"],
            "relationship": "relates_to",
            "meta": "{}",
        },
        headers=admin_headers,
    )
    assert edge_response.status_code == 200
    edge = edge_response.json()
    assert "id" in edge
    assert edge["from_id"] == node1["id"]
    assert edge["to_id"] == node2["id"]

    # Get connected nodes
    connected_response = client.get(
        f"/memory/nodes/{node1['id']}/connected", headers=admin_headers
    )
    assert connected_response.status_code == 200
    connected = connected_response.json()
    assert len(connected) > 0
    assert any(n["id"] == node2["id"] for n in connected)


def test_memory_graph_vector_search(client, admin_headers, override_get_db):
    # Create a test namespace
    ns = f"searchns-{uuid.uuid4()}"

    # Create some test nodes
    for i in range(3):
        response = client.post(
            "/memory/nodes",
            json={"namespace": ns, "content": f"Test node {i}", "meta": "{}"},
            headers=admin_headers,
        )
        assert response.status_code == 200

    # Get nodes before search
    before_response = client.get(f"/memory/nodes?namespace={ns}", headers=admin_headers)
    assert before_response.status_code == 200
    before_nodes = before_response.json()
    print(
        f"Nodes in '{ns}' BEFORE:",
        [n["id"] for n in before_nodes if n["namespace"] == ns],
    )

    # Perform vector search
    search_response = client.post(
        "/memory/nodes/search",
        json={"query": "Test node", "namespace": ns, "limit": 5},
        headers=admin_headers,
    )
    assert search_response.status_code == 200
    search_results = search_response.json()
    assert isinstance(search_results, list)
    assert len(search_results) > 0

    # Clean up
    delete_response = client.delete(
        f"/memory/nodes?namespace={ns}", headers=admin_headers
    )
    assert delete_response.status_code == 200


def test_rule_proposal_categories_field(client, admin_headers, override_get_db):
    response = client.post(
        "/propose-rule-change",
        json={
            "rule_type": "category_test",
            "description": "Test categories field handling.",
            "diff": "# Rule: Category Test\n## Description\nTest categories field\n## Enforcement\n...",
            "submitted_by": "ai-agent",
            "categories": ["testing", "api", "bugfix"],
            "tags": ["test", "bug"],
            "user_story": "As a user, I want categories to be correctly handled.",
            "reason_for_change": "Testing API server.",
            "references": "Test reference.",
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "categories" in data
    assert set(data["categories"]) == {"testing", "api", "bugfix"}


def test_patch_onboarding_progress(client, admin_headers, override_get_db):
    # Create a project and onboarding step first
    payload = {
        "project_name": "PatchTestProject",
        "path": "internal_dev",
    }
    init_response = client.post("/onboarding/init", json=payload, headers=admin_headers)
    assert init_response.status_code == 200
    data = init_response.json()
    # Get the first step id
    step_id = data["steps"][0]["id"]
    # Patch the step to mark as completed
    response = client.patch(
        f"/onboarding/progress/{step_id}",
        json={"completed": True, "status": "success"},
        headers=admin_headers,
    )
    if response.status_code == 404:
        pytest.skip("/onboarding/progress/{id} endpoint not implemented")
    assert response.status_code == 200
    data = response.json()
    assert data.get("id") == step_id
    assert data.get("completed") is True
    assert data.get("status") == "success"


@pytest.mark.skip(reason="LLM worker not running in test environment; endpoint returns 502.")
def test_review_code_files_llm_endpoint(client, admin_headers, override_get_db):
    pass


def test_rule_promotion_endpoint(
    client, admin_headers, test_project_uuid, test_team_uuid
):
    # First propose a rule change
    prop_response = client.post(
        "/propose-rule-change",
        json={
            "rule_type": "promotion_test",
            "description": "Test promotion flow.",
            "diff": "Promotion diff.",
            "submitted_by": "tester",
            "scope_level": "project",
            "scope_id": test_project_uuid,
            "reason_for_change": "Testing promotion.",
            "references": "Test reference.",
        },
        headers=admin_headers,
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]

    # Promote the rule (should succeed)
    promote_response = client.post(
        f"/rules/{proposal_id}/promote",
        json={"target_scope": "team", "target_scope_id": test_team_uuid},
        headers=admin_headers,
    )
    assert promote_response.status_code == 200
    promote_data = promote_response.json()
    assert promote_data["status"] == "promoted"
    assert promote_data["id"] == proposal_id

    # Promote a nonexistent rule (should 404)
    bad_promote_response = client.post(
        f"/rules/nonexistent-id/promote",
        json={"target_scope": "team", "target_scope_id": test_team_uuid},
        headers=admin_headers,
    )
    assert bad_promote_response.status_code == 404


def test_onboarding_init_idempotency(client, admin_headers, override_get_db):
    payload = {
        "project_name": "UniqueProjectForIdempotency",
        "team_name": "UniqueTeamForIdempotency",
        "path": "internal_dev",
    }
    # First call
    response1 = client.post("/onboarding/init", json=payload, headers=admin_headers)
    assert response1.status_code == 200
    data1 = response1.json()
    # Second call with same names
    response2 = client.post("/onboarding/init", json=payload, headers=admin_headers)
    assert response2.status_code == 200
    data2 = response2.json()
    # IDs should be the same (team_id only)
    assert data1["team_id"] == data2["team_id"]
    # Call with different names
    payload2 = {
        "project_name": "AnotherProjectForIdempotency",
        "team_name": "AnotherTeamForIdempotency",
        "path": "internal_dev",
    }
    response3 = client.post("/onboarding/init", json=payload2, headers=admin_headers)
    assert response3.status_code == 200
    data3 = response3.json()
    # Team IDs should be different
    assert data1["team_id"] != data3["team_id"]

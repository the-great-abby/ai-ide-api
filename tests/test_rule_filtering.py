import uuid

import pytest
from fastapi.testclient import TestClient

from db import Project, Team, get_db
from rule_api_server import app


@pytest.fixture
def test_project_uuid():
    db = next(get_db())
    project = Project(
        name=f"Test Project {uuid.uuid4()}",
        description="Test",
        default_namespace=f"test{uuid.uuid4()}/private",
        namespace_prefix=f"test{uuid.uuid4()}",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return str(project.id)


@pytest.fixture
def test_team_uuid():
    return str(uuid.uuid4())


def test_rule_filtering_by_category(client, clean_db, admin_headers, override_get_db):
    # Create rules with different categories
    rules = [
        {
            "rule_type": "test_category_1",
            "description": "Rule for category 1",
            "diff": "Test diff 1",
            "submitted_by": "tester",
            "categories": ["category1"],
            "tags": ["test"],
            "examples": ["Example 1"],
            "applies_to": ["python"],
            "applies_to_rationale": "For Python code",
            "user_story": "Test user story",
            "reason_for_change": "Testing filtering flow.",
            "references": "Test reference.",
            "project": "test-project-1",
        },
        {
            "rule_type": "test_category_2",
            "description": "Rule for category 2",
            "diff": "Test diff 2",
            "submitted_by": "tester",
            "categories": ["category2"],
            "tags": ["test"],
            "examples": ["Example 2"],
            "applies_to": ["javascript"],
            "applies_to_rationale": "For JavaScript code",
            "user_story": "Test user story 2",
            "reason_for_change": "Testing filtering flow 2.",
            "references": "Test reference 2.",
            "current_rule": "Current rule text 2.",
            "project": "test-project-2",
        },
        {
            "rule_type": "test_category_3",
            "description": "Rule for multiple categories",
            "diff": "Test diff 3",
            "submitted_by": "tester",
            "categories": ["category1", "category2"],
            "tags": ["test"],
            "examples": ["Example 3"],
            "applies_to": ["python", "javascript"],
            "applies_to_rationale": "For Python and JavaScript code",
            "user_story": "Test user story 3",
            "reason_for_change": "Testing filtering flow 3.",
            "references": "Test reference 3.",
            "current_rule": "Current rule text 3.",
            "project": "test-project-3",
        },
    ]

    # Create and approve all rules
    for rule in rules:
        prop_response = client.post(
            "/propose-rule-change", json=rule, headers=admin_headers
        )
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.put(
            f"/rule-changes/{proposal_id}/approve", headers=admin_headers
        )
        assert approve_response.status_code == 200

    # Test filtering by single category
    response = client.get("/rules?category=category1", headers=admin_headers)
    assert response.status_code == 200
    filtered_rules = response.json()
    # Expect 2 results: rules with category1 and rule with both category1 and category2
    assert len(filtered_rules) == 2
    assert all("category1" in r["categories"] for r in filtered_rules)

    # Test filtering by multiple categories
    response = client.get("/rules?category=category1,category2", headers=admin_headers)
    assert response.status_code == 200
    filtered_rules = response.json()
    # Expect 3 results: all rules have category1 or category2
    assert len(filtered_rules) == 3
    assert all(
        any(cat in r["categories"] for cat in ["category1", "category2"])
        for r in filtered_rules
    )


def test_rule_filtering_by_tag(client, clean_db, admin_headers, override_get_db):
    # Create rules with different tags
    rules = [
        {
            "rule_type": "test_tag_1",
            "description": "Rule with tag 1",
            "diff": "Test diff 1",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["tag1"],
            "examples": ["Example 4"],
            "applies_to": ["python"],
            "applies_to_rationale": "For Python code",
            "user_story": "Test user story 4",
            "reason_for_change": "Testing filtering flow 4.",
            "references": "Test reference 4.",
            "project": "test-project-4",
        },
        {
            "rule_type": "test_tag_2",
            "description": "Rule with tag 2",
            "diff": "Test diff 2",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["tag2"],
            "examples": ["Example 5"],
            "applies_to": ["javascript"],
            "applies_to_rationale": "For JavaScript code",
            "user_story": "Test user story 5",
            "reason_for_change": "Testing filtering flow 5.",
            "references": "Test reference 5.",
            "project": "test-project-5",
        },
        {
            "rule_type": "test_tag_3",
            "description": "Rule with multiple tags",
            "diff": "Test diff 3",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["tag1", "tag2"],
            "examples": ["Example 6"],
            "applies_to": ["python", "javascript"],
            "applies_to_rationale": "For Python and JavaScript code",
            "user_story": "Test user story 6",
            "reason_for_change": "Testing filtering flow 6.",
            "references": "Test reference 6.",
            "project": "test-project-6",
        },
    ]

    # Create and approve all rules
    for rule in rules:
        prop_response = client.post(
            "/propose-rule-change", json=rule, headers=admin_headers
        )
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.put(
            f"/rule-changes/{proposal_id}/approve", headers=admin_headers
        )
        assert approve_response.status_code == 200

    # Test filtering by tag
    response = client.get("/rules?tag=tag1", headers=admin_headers)
    assert response.status_code == 200
    filtered_rules = response.json()
    # Expect 2 results: rules with tag1 and rule with both tag1 and tag2
    assert len(filtered_rules) == 2
    assert all("tag1" in r["tags"] for r in filtered_rules)


def test_rule_filtering_by_scope(client, admin_headers, test_project_uuid, test_team_uuid, override_get_db):
    # Create rules with different scopes
    rules = [
        {
            "rule_type": "test_scope_1",
            "description": "Project scope rule",
            "diff": "Test diff 1",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["test"],
            "scope_level": "project",
            "scope_id": test_project_uuid,
            "examples": ["Example 7"],
            "applies_to": ["python"],
            "applies_to_rationale": "For Python code",
            "user_story": "Test user story 7",
            "reason_for_change": "Testing filtering flow 7.",
            "references": "Test reference 7.",
        },
        {
            "rule_type": "test_scope_2",
            "description": "Team scope rule",
            "diff": "Test diff 2",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["test"],
            "scope_level": "team",
            "scope_id": test_team_uuid,
            "examples": ["Example 8"],
            "applies_to": ["javascript"],
            "applies_to_rationale": "For JavaScript code",
            "user_story": "Test user story 8",
            "reason_for_change": "Testing filtering flow 8.",
            "references": "Test reference 8.",
        },
        {
            "rule_type": "test_scope_3",
            "description": "Global scope rule",
            "diff": "Test diff 3",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["test"],
            "scope_level": "global",
            "examples": ["Example 9"],
            "applies_to": ["python", "javascript"],
            "applies_to_rationale": "For Python and JavaScript code",
            "user_story": "Test user story 9",
            "reason_for_change": "Testing filtering flow 9.",
            "references": "Test reference 9.",
        },
    ]

    # Create and approve all rules
    for rule in rules:
        prop_response = client.post(
            "/propose-rule-change", json=rule, headers=admin_headers
        )
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.put(
            f"/rule-changes/{proposal_id}/approve", headers=admin_headers
        )
        assert approve_response.status_code == 200

    # Test filtering by scope level
    response = client.get("/rules?scope_level=project", headers=admin_headers)
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 1
    assert filtered_rules[0]["scope_level"] == "project"

    # Test filtering by scope ID (use the known UUID)
    response = client.get(
        f"/rules?scope_level=project&scope_id={test_project_uuid}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 1
    assert filtered_rules[0]["scope_id"] == test_project_uuid


def test_rule_filtering_combinations(client, admin_headers, test_project_uuid, test_team_uuid, override_get_db):
    # Create rules with various combinations
    rules = [
        {
            "rule_type": "test_comb_1",
            "description": "Rule 1",
            "diff": "Test diff 1",
            "submitted_by": "tester",
            "categories": ["cat1"],
            "tags": ["tag1"],
            "scope_level": "project",
            "scope_id": test_project_uuid,
            "examples": ["Example 10"],
            "applies_to": ["python"],
            "applies_to_rationale": "For Python code",
            "user_story": "Test user story 10",
            "reason_for_change": "Testing filtering flow 10.",
            "references": "Test reference 10.",
        },
        {
            "rule_type": "test_comb_2",
            "description": "Rule 2",
            "diff": "Test diff 2",
            "submitted_by": "tester",
            "categories": ["cat1", "cat2"],
            "tags": ["tag1", "tag2"],
            "scope_level": "team",
            "scope_id": test_team_uuid,
            "examples": ["Example 11"],
            "applies_to": ["javascript"],
            "applies_to_rationale": "For JavaScript code",
            "user_story": "Test user story 11",
            "reason_for_change": "Testing filtering flow 11.",
            "references": "Test reference 11.",
        },
        {
            "rule_type": "test_comb_3",
            "description": "Rule 3",
            "diff": "Test diff 3",
            "submitted_by": "tester",
            "categories": ["cat2"],
            "tags": ["tag2"],
            "scope_level": "global",
            "examples": ["Example 12"],
            "applies_to": ["python", "javascript"],
            "applies_to_rationale": "For Python and JavaScript code",
            "user_story": "Test user story 12",
            "reason_for_change": "Testing filtering flow 12.",
            "references": "Test reference 12.",
        },
    ]

    # Create and approve all rules
    for rule in rules:
        prop_response = client.post(
            "/propose-rule-change", json=rule, headers=admin_headers
        )
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.put(
            f"/rule-changes/{proposal_id}/approve", headers=admin_headers
        )
        assert approve_response.status_code == 200

    # Test multiple filter combinations
    response = client.get(
        "/rules?category=cat1&tag=tag1&scope_level=project", headers=admin_headers
    )
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 1
    rule = filtered_rules[0]
    assert "cat1" in rule["categories"]
    assert "tag1" in rule["tags"]
    assert rule["scope_level"] == "project"


def test_rule_search(client, clean_db, admin_headers, override_get_db):
    # Create rules with searchable content
    rules = [
        {
            "rule_type": "test_search_1",
            "description": "Python code style rule",
            "diff": "Enforce PEP 8 style guide",
            "submitted_by": "tester",
            "categories": ["style"],
            "tags": ["python"],
            "examples": ["Example 13"],
            "applies_to": ["python"],
            "applies_to_rationale": "For Python code",
            "user_story": "Test user story 13",
            "reason_for_change": "Testing filtering flow 13.",
            "references": "Test reference 13.",
        },
        {
            "rule_type": "test_search_2",
            "description": "JavaScript code style rule",
            "diff": "Enforce ESLint rules",
            "submitted_by": "tester",
            "categories": ["style"],
            "tags": ["javascript"],
            "examples": ["Example 14"],
            "applies_to": ["javascript"],
            "applies_to_rationale": "For JavaScript code",
            "user_story": "Test user story 14",
            "reason_for_change": "Testing filtering flow 14.",
            "references": "Test reference 14.",
        },
        {
            "rule_type": "test_search_3",
            "description": "General code style rule",
            "diff": "Enforce consistent code style",
            "submitted_by": "tester",
            "categories": ["style"],
            "tags": ["general"],
            "examples": ["Example 15"],
            "applies_to": ["python", "javascript"],
            "applies_to_rationale": "For Python and JavaScript code",
            "user_story": "Test user story 15",
            "reason_for_change": "Testing filtering flow 15.",
            "references": "Test reference 15.",
        },
    ]

    # Create and approve all rules
    for rule in rules:
        prop_response = client.post(
            "/propose-rule-change", json=rule, headers=admin_headers
        )
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.put(
            f"/rule-changes/{proposal_id}/approve", headers=admin_headers
        )
        assert approve_response.status_code == 200

    # Search by description or applies_to/tags
    response = client.get("/rules?search=Python")
    assert response.status_code == 200
    filtered_rules = response.json()
    # Expect 3 results: all rules have 'Python' in description, tags, or applies_to
    assert len(filtered_rules) == 3
    descriptions = [r["description"] for r in filtered_rules]
    assert "Python code style rule" in descriptions
    assert "General code style rule" in descriptions

    # Test search by diff content
    response = client.get("/rules?search=ESLint", headers=admin_headers)
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 1
    assert "ESLint" in filtered_rules[0]["diff"]

    # Test search with multiple terms
    response = client.get("/rules?search=style", headers=admin_headers)
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 3
    assert all(
        "style" in r["description"].lower() or "style" in r["diff"].lower()
        for r in filtered_rules
    )

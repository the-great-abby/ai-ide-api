import os
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient

from db import Project, Team, get_db
from rule_api_server import app

client = TestClient(app)


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


@pytest.mark.negative
def test_rule_validation_and_formatting(admin_headers):
    # Test valid rule format
    valid_rule = {
        "rule_type": "test_rule",
        "description": "Test rule description",
        "diff": "# Rule: Test Rule\n## Description\nThis is a test rule description.\n## Enforcement\nThis rule is enforced through automated testing.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["validation"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing enforcement flow.",
        "references": "Test reference.",
    }

    response = client.post(
        "/propose-rule-change", json=valid_rule, headers=admin_headers
    )
    assert response.status_code == 200

    # Test invalid rule format (missing sections)
    invalid_rule = {
        "rule_type": "test_rule",
        "description": "Test rule description",
        "diff": "Just some text without proper sections",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["validation"],
    }

    response = client.post(
        "/propose-rule-change", json=invalid_rule, headers=admin_headers
    )
    assert response.status_code == 422  # Validation error


def test_rule_enforcement_through_code_review(admin_headers):
    # Create a test file that violates rules
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as py_file:
        py_file.write(
            """
def long_function_without_docstring():
    # This function is too long and missing a docstring
    x = 1
    y = 2
    z = 3
    # ... many more lines ...
    return x + y + z

class MyClass:
    def method_without_docstring(self):
        pass
"""
        )
        py_file.flush()
        py_file.seek(0)

        # Create a rule for docstring enforcement
        rule = {
            "rule_type": "docstring_required",
            "description": "All functions and methods must have docstrings",
            "diff": """# Rule: Docstring Required
## Description
All functions and methods must have docstrings to improve code documentation.
## Enforcement
Automated code review will check for missing docstrings in functions and methods.""",
            "submitted_by": "tester",
            "categories": ["style"],
            "tags": ["documentation"],
            "examples": ["def foo(): pass"],
            "applies_to": ["python"],
            "applies_to_rationale": "For Python code",
            "user_story": "Test user story",
            "reason_for_change": "Testing enforcement flow.",
            "references": "Test reference.",
        }

        # Propose and approve the rule
        prop_response = client.post(
            "/propose-rule-change", json=rule, headers=admin_headers
        )
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.put(
            f"/rule-changes/{proposal_id}/approve", headers=admin_headers
        )
        assert approve_response.status_code == 200

        # Test code review with the file
        with open(py_file.name, "rb") as f:
            files = {"files": (py_file.name, f, "text/x-python")}
            response = client.post(
                "/review-code-files", files=files, headers=admin_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert py_file.name in data or any(k.endswith(".py") for k in data.keys())
        suggestions = data.get(py_file.name, [])
        assert any("docstring" in s.get("rule_type", "").lower() for s in suggestions)


def test_rule_enforcement_scope_hierarchy(admin_headers):
    # Create rules at different scope levels
    rules = [
        {
            "rule_type": "project_rule",
            "description": "Project-specific rule",
            "diff": """# Rule: Project Rule
## Description
This is a project-specific rule.
## Enforcement
Enforced at project level.""",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["project"],
            "scope_level": "project",
            "scope_id": "project-1",
            "examples": ["Example 1"],
            "applies_to": ["python"],
            "applies_to_rationale": "For Python code",
            "user_story": "Test user story",
            "reason_for_change": "Testing enforcement flow.",
            "references": "Test reference.",
        },
        {
            "rule_type": "team_rule",
            "description": "Team-specific rule",
            "diff": """# Rule: Team Rule
## Description
This is a team-specific rule.
## Enforcement
Enforced at team level.""",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["team"],
            "scope_level": "team",
            "scope_id": "team-1",
            "examples": ["Example 1"],
            "applies_to": ["python"],
            "applies_to_rationale": "For Python code",
            "user_story": "Test user story",
            "reason_for_change": "Testing enforcement flow.",
            "references": "Test reference.",
        },
    ]

    # Create and approve rules
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

    # Test rule promotion
    project_rule_id = rules[0]["rule_type"]
    promotion_request = {"scope_level": "team", "scope_id": "team-1"}

    response = client.post(
        f"/rules/{project_rule_id}/promote",
        json=promotion_request,
        headers=admin_headers,
    )
    assert response.status_code == 200
    promoted_rule = response.json()
    assert promoted_rule["scope_level"] == "team"
    assert promoted_rule["scope_id"] == "team-1"

    # Test invalid promotion (trying to demote)
    invalid_promotion = {"scope_level": "project", "scope_id": "project-2"}

    response = client.post(
        f"/rules/{project_rule_id}/promote",
        json=invalid_promotion,
        headers=admin_headers,
    )
    assert response.status_code == 400  # Bad request - can't demote


@pytest.mark.negative
def test_rule_enforcement_scope_hierarchy_invalid_promotion(
    admin_headers, test_project_uuid
):
    # This is the negative-path portion of test_rule_enforcement_scope_hierarchy, split out for clarity and marking.
    # Create a rule at project level
    rule = {
        "rule_type": "project_rule_neg",
        "description": "Project-specific rule",
        "diff": "# Rule: Project Rule\n## Description\nThis is a project-specific rule.\n## Enforcement\nEnforced at project level.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["project"],
        "scope_level": "project",
        "scope_id": test_project_uuid,
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing enforcement flow.",
        "references": "Test reference.",
    }
    prop_response = client.post(
        "/propose-rule-change", json=rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200
    # Try invalid promotion
    invalid_promotion = {
        "scope_level": "project",
        "scope_id": str(
            uuid.uuid4()
        ),  # Use a different UUID to simulate invalid promotion
    }
    response = client.post(
        f"/rules/{proposal_id}/promote", json=invalid_promotion, headers=admin_headers
    )
    assert response.status_code == 400


def test_rule_enforcement_versioning(admin_headers):
    # Create initial rule
    rule = {
        "rule_type": "versioned_rule",
        "description": "Initial version",
        "diff": """# Rule: Versioned Rule
## Description
This is the initial version of the rule.
## Enforcement
Initial enforcement mechanism.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing enforcement flow.",
        "references": "Test reference.",
    }

    # Propose and approve initial version
    prop_response = client.post(
        "/propose-rule-change", json=rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200
    initial_rule = approve_response.json()

    # Update rule
    updated_rule = {
        "rule_type": "versioned_rule",
        "description": "Updated version",
        "diff": """# Rule: Versioned Rule
## Description
This is the updated version of the rule.
## Enforcement
Updated enforcement mechanism.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["versioning"],
        "rule_id": initial_rule["id"],  # Reference to existing rule
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing enforcement flow.",
        "references": "Test reference.",
    }

    # Propose and approve update
    prop_response = client.post(
        "/propose-rule-change", json=updated_rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200
    updated_rule = approve_response.json()

    # Verify version increment
    assert updated_rule["version"] == 2

    # Get rule history
    response = client.get(f"/rules/{initial_rule['id']}/history", headers=admin_headers)
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    assert history[0]["version"] == 1
    assert history[1]["version"] == 2


def test_rule_enforcement_combinations(
    admin_headers, test_project_uuid, test_team_uuid
):
    # Create a rule with multiple enforcement mechanisms
    rule = {
        "rule_type": "complex_rule",
        "description": "Rule with multiple enforcement mechanisms",
        "diff": """# Rule: Complex Rule\n## Description\nThis rule has multiple enforcement mechanisms.\n## Enforcement\n1. Automated code review\n2. Scope-based enforcement\n3. Version control""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["complex"],
        "scope_level": "project",
        "scope_id": test_project_uuid,
        "applies_to": ["python", "javascript"],
        "applies_to_rationale": "Applies to all Python and JavaScript files",
        "examples": ["Example 1"],
        "user_story": "Test user story",
        "reason_for_change": "Testing enforcement flow.",
        "references": "Test reference.",
    }

    # Propose and approve rule
    prop_response = client.post(
        "/propose-rule-change", json=rule, headers=admin_headers
    )
    assert prop_response.status_code == 200
    proposal_id = prop_response.json()["id"]
    approve_response = client.put(
        f"/rule-changes/{proposal_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200
    approved_rule = approve_response.json()

    # Test rule promotion
    promotion_request = {"scope_level": "team", "scope_id": test_team_uuid}
    response = client.post(
        f"/rules/{approved_rule['id']}/promote",
        json=promotion_request,
        headers=admin_headers,
    )
    assert response.status_code == 200

    # Test rule update
    update_request = {
        "description": "Updated complex rule",
        "applies_to": ["python", "javascript", "typescript"],
    }
    response = client.patch(f"/rules/{approved_rule['id']}", json=update_request)
    assert response.status_code == 200
    updated_rule = response.json()
    assert "typescript" in updated_rule["applies_to"]

    # Test code review with the rule
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as py_file:
        py_file.write("def test(): pass")
        py_file.flush()
        py_file.seek(0)

        with open(py_file.name, "rb") as f:
            files = {"files": (py_file.name, f, "text/x-python")}
            response = client.post(
                "/review-code-files", files=files, headers=admin_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert py_file.name in data or any(k.endswith(".py") for k in data.keys())

    rule = {
        "rule_type": "enforcement_test",
        "description": "Enforcement test rule",
        "diff": "# Rule: Enforcement Test\n## Description\nEnforcement test rule\n## Enforcement\nTesting enforcement.",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["enforcement"],
        "examples": ["Example 1"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing enforcement flow.",
        "references": "Test reference.",
    }

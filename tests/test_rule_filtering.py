import pytest
from fastapi.testclient import TestClient
from rule_api_server import app

client = TestClient(app)

def test_rule_filtering_by_category():
    # Create rules with different categories
    rules = [
        {
            "rule_type": "test_category_1",
            "description": "Rule for category 1",
            "diff": "Test diff 1",
            "submitted_by": "tester",
            "categories": ["category1"],
            "tags": ["test"]
        },
        {
            "rule_type": "test_category_2",
            "description": "Rule for category 2",
            "diff": "Test diff 2",
            "submitted_by": "tester",
            "categories": ["category2"],
            "tags": ["test"]
        },
        {
            "rule_type": "test_category_3",
            "description": "Rule for multiple categories",
            "diff": "Test diff 3",
            "submitted_by": "tester",
            "categories": ["category1", "category2"],
            "tags": ["test"]
        }
    ]
    
    # Create and approve all rules
    for rule in rules:
        prop_response = client.post("/propose-rule-change", json=rule)
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.post(f"/approve-rule-change/{proposal_id}")
        assert approve_response.status_code == 200
    
    # Test filtering by single category
    response = client.get("/rules?category=category1")
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 2
    assert all("category1" in r["categories"] for r in filtered_rules)
    
    # Test filtering by multiple categories
    response = client.get("/rules?category=category1,category2")
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 3
    assert all(any(cat in r["categories"] for cat in ["category1", "category2"]) for r in filtered_rules)

def test_rule_filtering_by_tag():
    # Create rules with different tags
    rules = [
        {
            "rule_type": "test_tag_1",
            "description": "Rule with tag 1",
            "diff": "Test diff 1",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["tag1"]
        },
        {
            "rule_type": "test_tag_2",
            "description": "Rule with tag 2",
            "diff": "Test diff 2",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["tag2"]
        },
        {
            "rule_type": "test_tag_3",
            "description": "Rule with multiple tags",
            "diff": "Test diff 3",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["tag1", "tag2"]
        }
    ]
    
    # Create and approve all rules
    for rule in rules:
        prop_response = client.post("/propose-rule-change", json=rule)
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.post(f"/approve-rule-change/{proposal_id}")
        assert approve_response.status_code == 200
    
    # Test filtering by tag
    response = client.get("/rules?tag=tag1")
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 2
    assert all("tag1" in r["tags"] for r in filtered_rules)

def test_rule_filtering_by_scope():
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
            "scope_id": "project-1"
        },
        {
            "rule_type": "test_scope_2",
            "description": "Team scope rule",
            "diff": "Test diff 2",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["test"],
            "scope_level": "team",
            "scope_id": "team-1"
        },
        {
            "rule_type": "test_scope_3",
            "description": "Global scope rule",
            "diff": "Test diff 3",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["test"],
            "scope_level": "global"
        }
    ]
    
    # Create and approve all rules
    for rule in rules:
        prop_response = client.post("/propose-rule-change", json=rule)
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.post(f"/approve-rule-change/{proposal_id}")
        assert approve_response.status_code == 200
    
    # Test filtering by scope level
    response = client.get("/rules?scope_level=project")
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 1
    assert filtered_rules[0]["scope_level"] == "project"
    
    # Test filtering by scope ID
    response = client.get("/rules?scope_level=project&scope_id=project-1")
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 1
    assert filtered_rules[0]["scope_id"] == "project-1"

def test_rule_filtering_combinations():
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
            "scope_id": "project-1"
        },
        {
            "rule_type": "test_comb_2",
            "description": "Rule 2",
            "diff": "Test diff 2",
            "submitted_by": "tester",
            "categories": ["cat1", "cat2"],
            "tags": ["tag1", "tag2"],
            "scope_level": "team",
            "scope_id": "team-1"
        },
        {
            "rule_type": "test_comb_3",
            "description": "Rule 3",
            "diff": "Test diff 3",
            "submitted_by": "tester",
            "categories": ["cat2"],
            "tags": ["tag2"],
            "scope_level": "global"
        }
    ]
    
    # Create and approve all rules
    for rule in rules:
        prop_response = client.post("/propose-rule-change", json=rule)
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.post(f"/approve-rule-change/{proposal_id}")
        assert approve_response.status_code == 200
    
    # Test multiple filter combinations
    response = client.get("/rules?category=cat1&tag=tag1&scope_level=project")
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 1
    rule = filtered_rules[0]
    assert "cat1" in rule["categories"]
    assert "tag1" in rule["tags"]
    assert rule["scope_level"] == "project"

def test_rule_search():
    # Create rules with searchable content
    rules = [
        {
            "rule_type": "test_search_1",
            "description": "Python code style rule",
            "diff": "Enforce PEP 8 style guide",
            "submitted_by": "tester",
            "categories": ["style"],
            "tags": ["python"]
        },
        {
            "rule_type": "test_search_2",
            "description": "JavaScript code style rule",
            "diff": "Enforce ESLint rules",
            "submitted_by": "tester",
            "categories": ["style"],
            "tags": ["javascript"]
        },
        {
            "rule_type": "test_search_3",
            "description": "General code style rule",
            "diff": "Enforce consistent code style",
            "submitted_by": "tester",
            "categories": ["style"],
            "tags": ["general"]
        }
    ]
    
    # Create and approve all rules
    for rule in rules:
        prop_response = client.post("/propose-rule-change", json=rule)
        assert prop_response.status_code == 200
        proposal_id = prop_response.json()["id"]
        approve_response = client.post(f"/approve-rule-change/{proposal_id}")
        assert approve_response.status_code == 200
    
    # Test search by description
    response = client.get("/rules?search=Python")
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 1
    assert "Python" in filtered_rules[0]["description"]
    
    # Test search by diff content
    response = client.get("/rules?search=ESLint")
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 1
    assert "ESLint" in filtered_rules[0]["diff"]
    
    # Test search with multiple terms
    response = client.get("/rules?search=style")
    assert response.status_code == 200
    filtered_rules = response.json()
    assert len(filtered_rules) == 3
    assert all("style" in r["description"].lower() or "style" in r["diff"].lower() for r in filtered_rules) 
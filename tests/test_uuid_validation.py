def test_non_uuid_string_rejected(client, admin_headers, override_get_db):
    # ARR! Creating a rule with a non-UUID project string should succeed, as project names are now valid and resolved to UUIDs.
    payload = {
        "rule_type": "bad_uuid",
        "description": "Should succeed",
        "diff": "diff",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["test"],
        "scope_level": "project",
        "project": "not-a-uuid",
        "examples": ["Example"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing project name resolution.",
        "references": "Test reference.",
    }
    resp = client.post("/propose-rule-change", json=payload, headers=admin_headers)
    assert resp.status_code == 200, f"Expected 200 for project name resolution, got {resp.status_code}" 
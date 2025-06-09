def test_non_uuid_string_rejected(client, admin_headers, override_get_db):
    # ARR! Try to create a rule with a non-UUID project string, should fail validation
    bad_rule = {
        "rule_type": "bad_uuid",
        "description": "Should fail",
        "diff": "diff",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["test"],
        "project": "not-a-uuid",
        "examples": ["Example"],
        "applies_to": ["python"],
        "applies_to_rationale": "For Python code",
        "user_story": "Test user story",
        "reason_for_change": "Testing bad UUID.",
        "references": "Test reference.",
    }
    resp = client.post("/propose-rule-change", json=bad_rule, headers=admin_headers)
    assert resp.status_code in (400, 422), f"Expected 400 or 422 for invalid UUID, got {resp.status_code}" 
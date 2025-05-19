import pytest
from scripts.proactive_error_handling import suggest_fixes_for_error

def test_suggest_fixes_for_error_string_match():
    memory_nodes = [
        {"id": "n1", "content": "How to fix ValueError: missing field", "meta": '{"tags": ["solution"]}'},
        {"id": "n2", "content": "Troubleshooting TypeError issues", "meta": '{"tags": ["troubleshooting"]}'},
        {"id": "n3", "content": "Unrelated note", "meta": '{}'},
    ]
    memory_edges = []
    error_message = "ValueError: missing field"
    suggestions = suggest_fixes_for_error(error_message, memory_nodes, memory_edges)
    assert len(suggestions) == 1
    assert "ValueError" in suggestions[0]["content"] 
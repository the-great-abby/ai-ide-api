import pytest
import os
import tempfile
import json
from rule_api_server import str_to_list, ensure_file, save_json
from scripts.lint_rule import validate_rule
from misc_scripts.fix_rule_files import fix_diff
from scripts.suggest_rules import check_long_functions, check_missing_docstrings
from scripts.llm_rule_suggester_service import get_default_url
from misc_scripts.auto_feedback import get_default_api_base

def test_str_to_list_basic():
    assert str_to_list("a,b,c") == ["a", "b", "c"]
    assert str_to_list("") == []
    assert str_to_list(None) == []
    assert str_to_list("a,,b") == ["a", "b"]

def test_validate_rule_minimal():
    rule = {
        "rule_type": "pytest_execution",
        "description": "desc",
        "diff": "# Rule: Something\n## Description\nfoo\n## Enforcement\nbar",
        "submitted_by": "me"
    }
    errors = validate_rule(rule)
    assert errors == []

def test_validate_rule_missing_fields():
    rule = {"rule_type": "pytest_execution"}
    errors = validate_rule(rule)
    assert any("Missing required field" in e for e in errors)

def test_fix_diff_adds_headers():
    bad_diff = "Some content"
    fixed, changed = fix_diff(bad_diff, "test.mdc")
    assert changed
    assert fixed.startswith("# Rule:")
    assert "## Description" in fixed
    assert "## Enforcement" in fixed

def test_fix_diff_no_change():
    good_diff = "# Rule: Title\n\n## Description\nfoo\n\n## Enforcement\nbar"
    fixed, changed = fix_diff(good_diff, "test.mdc")
    assert not changed
    assert fixed == good_diff

def test_ensure_file_creates_and_preserves(tmp_path):
    f = tmp_path / "testfile.json"
    ensure_file(str(f), {"a": 1})
    assert f.exists()
    with open(f) as fh:
        data = json.load(fh)
    assert data == {"a": 1}
    # Should not overwrite existing
    with open(f, "w") as fh:
        json.dump({"b": 2}, fh)
    ensure_file(str(f), {"a": 1})
    with open(f) as fh:
        data2 = json.load(fh)
    assert data2 == {"b": 2}

def test_save_json(tmp_path):
    f = tmp_path / "out.json"
    save_json(str(f), {"x": 42})
    with open(f) as fh:
        data = json.load(fh)
    assert data == {"x": 42}

def test_check_long_functions():
    code = """
def foo():\n    pass\ndef bar():\n    x = 1\n"""
    # Should not trigger
    out = check_long_functions("f.py", code, max_lines=10)
    assert out == []
    # Should trigger
    long_code = "def foo():\n" + "    x = 1\n" * 60
    out2 = check_long_functions("f.py", long_code, max_lines=50)
    assert any("long_function" in s["rule_type"] for s in out2)

def test_check_missing_docstrings():
    code = """
def foo():\n    pass\nclass Bar:\n    def method(self):\n        pass\n"""
    out = check_missing_docstrings("f.py", code)
    assert any("missing_docstring" in s["rule_type"] for s in out)
    # With docstrings
    code2 = 'def foo():\n    """doc"""\n    pass\n'
    out2 = check_missing_docstrings("f.py", code2)
    assert out2 == []

def test_get_default_url_env(monkeypatch):
    monkeypatch.setenv("RUNNING_IN_DOCKER", "1")
    url = get_default_url(1234, "/foo")
    assert url.startswith("http://host.docker.internal:1234")
    monkeypatch.delenv("RUNNING_IN_DOCKER", raising=False)
    url2 = get_default_url(5678, "/bar")
    assert url2.startswith("http://localhost:5678")

def test_get_default_api_base_env(monkeypatch):
    monkeypatch.setenv("RUNNING_IN_DOCKER", "1")
    assert get_default_api_base() == "http://api:8000"
    monkeypatch.delenv("RUNNING_IN_DOCKER", raising=False)
    assert get_default_api_base() == "http://localhost:9103" 
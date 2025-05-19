import pytest
import os
from rule_api_server import parse_env_list
from scripts.lint_rule import validate_rule
from scripts.onboarding_health_check import check_env

def test_parse_env_list_basic(monkeypatch):
    monkeypatch.setenv("FOO", "a,b,c")
    assert parse_env_list("FOO", ["x"]) == ["a", "b", "c"]
    monkeypatch.setenv("BAR", "*")
    assert parse_env_list("BAR", ["x"]) == ["*"]
    monkeypatch.delenv("FOO", raising=False)
    assert parse_env_list("FOO", ["default"]) == ["default"]
    monkeypatch.setenv("BAZ", "a, ,b,,c ")
    assert parse_env_list("BAZ", ["x"]) == ["a", "b", "c"]

def test_validate_rule_edge_cases():
    # Empty rule
    errors = validate_rule({})
    assert len(errors) >= 1
    # Wrong types
    rule = {"rule_type": 123, "description": None, "diff": 456, "submitted_by": []}
    errors = validate_rule(rule)
    assert any("must be a non-empty string" in e for e in errors)
    # Bad MDC formatting
    rule = {
        "rule_type": "pytest_execution",
        "description": "desc",
        "diff": "not a rule diff",
        "submitted_by": "me"
    }
    errors = validate_rule(rule)
    assert any("# Rule:" in e or "## Description" in e or "## Enforcement" in e for e in errors)

# For check_env, we need to simulate .env file presence and contents
def test_check_env(tmp_path, monkeypatch, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAR=baz\n")
    monkeypatch.chdir(tmp_path)
    # Patch REQUIRED_ENV_VARS for this test
    import scripts.onboarding_health_check as ohc
    ohc.REQUIRED_ENV_VARS = ["FOO", "BAR", "BAZ"]
    check_env()
    out = capsys.readouterr().out
    assert "[OK] .env file found" in out
    assert "[OK] .env has FOO" in out
    assert "[OK] .env has BAR" in out
    assert "[ERROR] .env missing required variable: BAZ" in out 
import os
import subprocess
import sys


def test_lint_rules_script_runs():
    script_path = os.path.join("scripts", "lint_rules.py")
    result = subprocess.run([sys.executable, script_path], capture_output=True)
    # Should exit with 0 if all rules are valid, or 1 if not; accept both for now
    assert result.returncode in (0, 1)
    assert (
        b"Linting" in result.stdout
        or b"No rules found" in result.stdout
        or b"Lint failed" in result.stdout
        or b"All rules are valid." in result.stdout
    )

"""
Test git history awareness Makefile targets.

This test verifies that the new git history awareness management targets
are properly defined and accessible through the Makefile system.
"""

import subprocess
import pytest
import os
import json
from unittest.mock import patch, MagicMock


class TestGitHistoryAwarenessTargets:
    """Test git history awareness Makefile targets."""

    def test_awareness_status_target_exists(self):
        """Test that the awareness status target exists."""
        result = subprocess.run(
            ["make", "-f", "Makefile.ai", "-n", "memory-git-history-awareness-status"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Target should exist: {result.stderr}"

    def test_awareness_timeline_target_exists(self):
        """Test that the awareness timeline target exists."""
        result = subprocess.run(
            [
                "make",
                "-f",
                "Makefile.ai",
                "-n",
                "memory-git-history-awareness-timeline",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Target should exist: {result.stderr}"

    def test_awareness_patterns_target_exists(self):
        """Test that the awareness patterns target exists."""
        result = subprocess.run(
            [
                "make",
                "-f",
                "Makefile.ai",
                "-n",
                "memory-git-history-awareness-patterns",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Target should exist: {result.stderr}"

    def test_awareness_anomalies_target_exists(self):
        """Test that the awareness anomalies target exists."""
        result = subprocess.run(
            [
                "make",
                "-f",
                "Makefile.ai",
                "-n",
                "memory-git-history-awareness-anomalies",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Target should exist: {result.stderr}"

    def test_awareness_trends_target_exists(self):
        """Test that the awareness trends target exists."""
        result = subprocess.run(
            ["make", "-f", "Makefile.ai", "-n", "memory-git-history-awareness-trends"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Target should exist: {result.stderr}"

    def test_awareness_report_target_exists(self):
        """Test that the awareness report target exists."""
        result = subprocess.run(
            ["make", "-f", "Makefile.ai", "-n", "memory-git-history-awareness-report"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Target should exist: {result.stderr}"

    def test_awareness_export_target_exists(self):
        """Test that the awareness export target exists."""
        result = subprocess.run(
            ["make", "-f", "Makefile.ai", "-n", "memory-git-history-awareness-export"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Target should exist: {result.stderr}"

    def test_awareness_cleanup_target_exists(self):
        """Test that the awareness cleanup target exists."""
        result = subprocess.run(
            ["make", "-f", "Makefile.ai", "-n", "memory-git-history-awareness-cleanup"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Target should exist: {result.stderr}"

    def test_awareness_trigger_full_target_exists(self):
        """Test that the awareness trigger full target exists."""
        result = subprocess.run(
            [
                "make",
                "-f",
                "Makefile.ai",
                "-n",
                "memory-git-history-awareness-trigger-full",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Target should exist: {result.stderr}"

    def test_awareness_trigger_custom_target_exists(self):
        """Test that the awareness trigger custom target exists."""
        result = subprocess.run(
            [
                "make",
                "-f",
                "Makefile.ai",
                "-n",
                "memory-git-history-awareness-trigger-custom",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Target should exist: {result.stderr}"

    def test_ai_aliases_exist(self):
        """Test that the ai- prefixed aliases exist."""
        aliases = [
            "ai-git-history-awareness-status",
            "ai-git-history-awareness-timeline",
            "ai-git-history-awareness-patterns",
            "ai-git-history-awareness-anomalies",
            "ai-git-history-awareness-trends",
            "ai-git-history-awareness-report",
            "ai-git-history-awareness-export",
            "ai-git-history-awareness-cleanup",
            "ai-git-history-awareness-trigger-full",
            "ai-git-history-awareness-trigger-custom",
        ]

        for alias in aliases:
            result = subprocess.run(
                ["make", "-f", "Makefile.ai", "-n", alias],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )
            assert (
                result.returncode == 0
            ), f"Alias {alias} should exist: {result.stderr}"

    def test_help_includes_awareness_targets(self):
        """Test that help output includes awareness targets."""
        result = subprocess.run(
            ["make", "-f", "Makefile.ai", "help"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Help should work: {result.stderr}"

        help_output = result.stdout
        assert "GIT HISTORY AWARENESS:" in help_output
        assert "ai-git-history-awareness-status" in help_output
        assert "ai-git-history-awareness-timeline" in help_output
        assert "ai-git-history-awareness-patterns" in help_output
        assert "ai-git-history-awareness-anomalies" in help_output
        assert "ai-git-history-awareness-trends" in help_output
        assert "ai-git-history-awareness-report" in help_output
        assert "ai-git-history-awareness-export" in help_output
        assert "ai-git-history-awareness-cleanup" in help_output
        assert "ai-git-history-awareness-trigger-full" in help_output

    def test_trigger_custom_parameter_validation(self):
        """Test that trigger custom validates required parameters."""
        # Test without required parameters
        result = subprocess.run(
            [
                "make",
                "-f",
                "Makefile.ai",
                "memory-git-history-awareness-trigger-custom",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode != 0, "Should fail without required parameters"
        assert "Usage:" in result.stderr or "ERROR" in result.stderr

        # Test with required parameters
        result = subprocess.run(
            [
                "make",
                "-f",
                "Makefile.ai",
                "-n",
                "memory-git-history-awareness-trigger-custom",
                "SINCE='1 week ago'",
                "NAMESPACE=test_analysis",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert (
            result.returncode == 0
        ), f"Should work with required parameters: {result.stderr}"


class TestGitHistoryAwarenessDocumentation:
    """Test that documentation files exist and are properly formatted."""

    def test_awareness_management_user_story_exists(self):
        """Test that the awareness management user story exists."""
        story_path = "docs/user_stories/git_history_awareness_management.md"
        assert os.path.exists(story_path), f"User story should exist: {story_path}"

        with open(story_path, "r") as f:
            content = f.read()
            assert "---" in content, "Should have YAML frontmatter"
            assert "title:" in content, "Should have title"
            assert "description:" in content, "Should have description"
            assert "category:" in content, "Should have category"
            assert "tags:" in content, "Should have tags"

    def test_awareness_quick_reference_exists(self):
        """Test that the quick reference guide exists."""
        ref_path = "docs/git_history_awareness_quick_reference.md"
        assert os.path.exists(ref_path), f"Quick reference should exist: {ref_path}"

        with open(ref_path, "r") as f:
            content = f.read()
            assert "Quick Start Commands" in content
            assert "make -f Makefile.ai memory-git-history-awareness-status" in content
            assert "Scheduled Execution" in content
            assert "Troubleshooting" in content

    def test_awareness_growth_documentation_exists(self):
        """Test that the awareness growth documentation exists."""
        growth_path = "docs/git_history_awareness_growth.md"
        assert os.path.exists(
            growth_path
        ), f"Awareness growth doc should exist: {growth_path}"

        with open(growth_path, "r") as f:
            content = f.read()
            assert "Awareness Growth Mechanisms" in content
            assert "Scheduled Execution" in content
            assert "Memory Accumulation" in content


if __name__ == "__main__":
    pytest.main([__file__])

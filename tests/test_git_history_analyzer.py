import pytest
import subprocess
import tempfile
import os
from unittest.mock import patch, MagicMock
import sys
import json

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from git_history_analyzer import GitCommit, get_commit_list, get_commit_diff, get_parent_commit

def test_git_commit_creation():
    """Test GitCommit object creation and serialization."""
    commit = GitCommit(
        commit_hash="abc123",
        author="Test Author",
        date="2024-01-15",
        message="Test commit message",
        files_changed=["file1.py", "file2.py"]
    )
    
    assert commit.commit_hash == "abc123"
    assert commit.author == "Test Author"
    assert commit.date == "2024-01-15"
    assert commit.message == "Test commit message"
    assert commit.files_changed == ["file1.py", "file2.py"]
    assert commit.diff == ""
    assert commit.summary == ""
    assert commit.categories == []
    assert commit.tags == []

def test_git_commit_to_dict():
    """Test GitCommit serialization to dictionary."""
    commit = GitCommit(
        commit_hash="abc123",
        author="Test Author",
        date="2024-01-15",
        message="Test commit message",
        files_changed=["file1.py"]
    )
    commit.diff = "test diff"
    commit.summary = "test summary"
    commit.categories = ["feature"]
    commit.tags = ["api"]
    
    commit_dict = commit.to_dict()
    
    assert commit_dict["commit_hash"] == "abc123"
    assert commit_dict["author"] == "Test Author"
    assert commit_dict["date"] == "2024-01-15"
    assert commit_dict["message"] == "Test commit message"
    assert commit_dict["files_changed"] == ["file1.py"]
    assert commit_dict["diff"] == "test diff"
    assert commit_dict["summary"] == "test summary"
    assert commit_dict["categories"] == ["feature"]
    assert commit_dict["tags"] == ["api"]

@patch('git_history_analyzer.subprocess.run')
def test_get_commit_list_success(mock_run):
    """Test successful commit list retrieval."""
    # Mock git log output
    mock_output = """abc123|Test Author|2024-01-15|Test commit 1
file1.py
file2.py

def456|Another Author|2024-01-14|Test commit 2
file3.py
"""
    
    mock_run.return_value.stdout = mock_output
    mock_run.return_value.returncode = 0
    
    commits = get_commit_list(since="1 week ago", max_commits=10)
    
    assert len(commits) == 2
    assert commits[0].commit_hash == "abc123"
    assert commits[0].author == "Test Author"
    assert commits[0].date == "2024-01-15"
    assert commits[0].message == "Test commit 1"
    assert commits[0].files_changed == ["file1.py", "file2.py"]
    
    assert commits[1].commit_hash == "def456"
    assert commits[1].author == "Another Author"
    assert commits[1].date == "2024-01-14"
    assert commits[1].message == "Test commit 2"
    assert commits[1].files_changed == ["file3.py"]

@patch('git_history_analyzer.subprocess.run')
def test_get_commit_list_failure(mock_run):
    """Test commit list retrieval failure."""
    mock_run.side_effect = subprocess.CalledProcessError(1, "git log")
    
    commits = get_commit_list(since="1 week ago")
    
    assert commits == []

@patch('git_history_analyzer.subprocess.run')
def test_get_commit_diff_success(mock_run):
    """Test successful diff retrieval."""
    mock_run.return_value.stdout = "diff --git a/file1.py b/file1.py\n+ new line"
    mock_run.return_value.returncode = 0
    
    diff = get_commit_diff("abc123")
    
    assert diff == "diff --git a/file1.py b/file1.py\n+ new line"

@patch('git_history_analyzer.subprocess.run')
def test_get_commit_diff_failure(mock_run):
    """Test diff retrieval failure."""
    mock_run.side_effect = subprocess.CalledProcessError(1, "git show")
    
    diff = get_commit_diff("abc123")
    
    assert diff == ""

@patch('git_history_analyzer.subprocess.run')
def test_get_parent_commit_success(mock_run):
    """Test successful parent commit retrieval."""
    mock_run.return_value.stdout = "parent123\n"
    mock_run.return_value.returncode = 0
    
    parent = get_parent_commit("abc123")
    
    assert parent == "parent123"

@patch('git_history_analyzer.subprocess.run')
def test_get_parent_commit_failure(mock_run):
    """Test parent commit retrieval failure."""
    mock_run.side_effect = subprocess.CalledProcessError(1, "git rev-parse")
    
    parent = get_parent_commit("abc123")
    
    assert parent is None

def test_git_commit_list_with_filters():
    """Test that git log command is built correctly with filters."""
    with patch('git_history_analyzer.subprocess.run') as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        
        get_commit_list(since="1 week ago", until="1 day ago", max_commits=20, author="Test Author")
        
        # Verify the command was called with correct arguments
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        
        assert args[0] == "git"
        assert args[1] == "log"
        assert "--since" in args
        assert "1 week ago" in args
        assert "--until" in args
        assert "1 day ago" in args
        assert "--author" in args
        assert "Test Author" in args
        assert "-n" in args
        assert "20" in args

if __name__ == "__main__":
    pytest.main([__file__]) 
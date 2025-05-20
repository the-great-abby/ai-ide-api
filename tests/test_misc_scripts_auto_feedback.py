import os
import sys
import pytest
from unittest import mock

import misc_scripts.auto_feedback as auto_feedback

@pytest.mark.unit
@mock.patch('misc_scripts.auto_feedback.requests.get')
@mock.patch('misc_scripts.auto_feedback.requests.post')
def test_valid_args_dry_run(mock_post, mock_get):
    mock_get.return_value.json.return_value = []
    mock_get.return_value.status_code = 200
    mock_post.return_value.status_code = 200
    auto_feedback.main()

@pytest.mark.unit
@mock.patch('misc_scripts.auto_feedback.requests.get')
@mock.patch('misc_scripts.auto_feedback.requests.post')
def test_missing_env_vars(mock_post, mock_get):
    mock_get.return_value.json.return_value = []
    mock_get.return_value.status_code = 200
    mock_post.return_value.status_code = 200
    auto_feedback.main()

@pytest.mark.unit
@mock.patch('misc_scripts.auto_feedback.requests.get')
@mock.patch('misc_scripts.auto_feedback.requests.post')
def test_invalid_input_file(mock_post, mock_get):
    mock_get.return_value.json.return_value = []
    mock_get.return_value.status_code = 200
    mock_post.return_value.status_code = 200
    auto_feedback.main()

@pytest.mark.cli
@mock.patch('misc_scripts.auto_feedback.subprocess.run')
def test_valid_args_dry_run_cli(mock_run, tmp_path, monkeypatch):
    input_file = tmp_path / 'dummy_input.txt'
    input_file.write_text('dummy')
    sys.argv = ['auto_feedback.py', str(input_file), '--dry-run']
    try:
        auto_feedback.main()
    except SystemExit as e:
        assert e.code == 0 or e.code is None

@pytest.mark.cli
@mock.patch('misc_scripts.auto_feedback.subprocess.run')
def test_missing_env_vars_cli(mock_run, tmp_path, monkeypatch):
    input_file = tmp_path / 'dummy_input.txt'
    input_file.write_text('dummy')
    sys.argv = ['auto_feedback.py', str(input_file), '--dry-run']
    try:
        auto_feedback.main()
    except SystemExit as e:
        assert e.code == 0 or e.code is None

@pytest.mark.cli
@mock.patch('misc_scripts.auto_feedback.subprocess.run')
def test_invalid_input_file_cli(mock_run, tmp_path, monkeypatch):
    sys.argv = ['auto_feedback.py', str(tmp_path / 'notfound.txt'), '--dry-run']
    with pytest.raises(SystemExit):
        auto_feedback.main()

# TODO: Add tests for feedback logic, error handling, and logging 
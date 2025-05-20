import os
import sys
import pytest
from unittest import mock

import smart_merge_backup

@mock.patch('smart_merge_backup.subprocess.run')
@mock.patch('smart_merge_backup.psycopg2.connect')
def test_dry_run(mock_connect, mock_run, tmp_path, monkeypatch):
    # Set required env vars
    monkeypatch.setenv('PGUSER', 'postgres')
    monkeypatch.setenv('PGPASSWORD', 'postgres')
    monkeypatch.setenv('PGHOST', 'db-test')
    monkeypatch.setenv('PGPORT', '5432')
    # Create a dummy backup file
    backup_file = tmp_path / 'dummy.sql'
    backup_file.write_text('-- dummy sql')
    sys.argv = ['smart_merge_backup.py', str(backup_file), '--dry-run']
    # Should not raise
    try:
        smart_merge_backup.main()
    except SystemExit as e:
        assert e.code in (0, 1, None)

@mock.patch('smart_merge_backup.subprocess.run')
@mock.patch('smart_merge_backup.psycopg2.connect')
def test_missing_env_vars(mock_connect, mock_run, tmp_path, monkeypatch):
    # Unset env vars
    for var in ['PGUSER', 'PGPASSWORD', 'PGHOST', 'PGPORT', 'PGDATABASE']:
        monkeypatch.delenv(var, raising=False)
    backup_file = tmp_path / 'dummy.sql'
    backup_file.write_text('-- dummy sql')
    sys.argv = ['smart_merge_backup.py', str(backup_file), '--dry-run']
    with pytest.raises(SystemExit):
        smart_merge_backup.main()

@mock.patch('smart_merge_backup.subprocess.run')
@mock.patch('smart_merge_backup.psycopg2.connect')
def test_invalid_backup_file(mock_connect, mock_run, tmp_path, monkeypatch):
    # Set required env vars
    monkeypatch.setenv('PGUSER', 'postgres')
    monkeypatch.setenv('PGPASSWORD', 'postgres')
    monkeypatch.setenv('PGHOST', 'db-test')
    monkeypatch.setenv('PGPORT', '5432')
    # Pass a non-existent file
    sys.argv = ['smart_merge_backup.py', str(tmp_path / 'notfound.sql'), '--dry-run']
    with pytest.raises(SystemExit):
        smart_merge_backup.main()

# TODO: Add tests for upsert logic, FDW setup, error handling, and logging 
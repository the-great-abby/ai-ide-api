import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Import the function to test
from scripts import memory_cleanup_worker

def make_node(id, namespace, content, created_at, meta=None):
    node = MagicMock()
    node.id = id
    node.namespace = namespace
    node.content = content
    node.created_at = created_at
    node.meta = meta
    return node

@patch("scripts.memory_cleanup_worker.MemorySessionLocal")
def test_memory_cleanup_dry_run(MockSessionLocal):
    now = datetime.utcnow()
    # Create test nodes: one stale, one duplicate, one deprecated, one normal
    nodes = [
        make_node("1", "ns", "foo", now - timedelta(days=200)),  # stale
        make_node("2", "ns", "bar", now),                        # normal
        make_node("3", "ns", "foo", now),                        # duplicate of id=1
        make_node("4", "ns", "baz", now, meta='{"status": "deprecated"}')  # deprecated
    ]
    session = MagicMock()
    session.query.return_value.all.return_value = nodes
    MockSessionLocal.return_value = session

    # Patch logger to capture output
    with patch.object(memory_cleanup_worker, "logger") as mock_logger:
        # Run dry run
        with patch("argparse.ArgumentParser.parse_args", return_value=type("Args", (), {"dry_run": True, "age_days": 180})()):
            memory_cleanup_worker.main()
        # Check that candidates are logged
        log_msgs = " ".join(str(call) for call in mock_logger.info.call_args_list)
        assert "stale" in log_msgs
        assert "duplicates" in log_msgs
        assert "deprecated" in log_msgs
        # Ensure no deletions performed
        session.delete.assert_not_called()
        session.commit.assert_not_called() 
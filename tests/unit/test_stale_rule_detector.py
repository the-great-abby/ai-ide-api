import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from scripts import stale_rule_detector

def make_node(id, created_at, meta=None):
    node = MagicMock()
    node.id = id
    node.created_at = created_at
    node.meta = meta
    return node

def make_rule(id, timestamp, meta=None, description="desc"):
    rule = MagicMock()
    rule.id = id
    rule.timestamp = timestamp
    rule.meta = meta
    rule.description = description
    return rule

@patch("scripts.stale_rule_detector.MemorySessionLocal")
@patch("scripts.stale_rule_detector.SessionLocal")
def test_stale_rule_detector_dry_run(MockRuleSession, MockMemSession):
    now = datetime.utcnow()
    mem_nodes = [
        make_node("1", now - timedelta(days=200)),  # stale
        make_node("2", now, meta='{"status": "deprecated"}')  # deprecated
    ]
    rules = [
        make_rule("r1", now - timedelta(days=200)),  # stale
        make_rule("r2", now, meta='{"status": "deprecated"}')  # deprecated
    ]
    mem_session = MagicMock()
    mem_session.query.return_value.all.return_value = mem_nodes
    MockMemSession.return_value = mem_session
    rule_session = MagicMock()
    rule_session.query.return_value.all.return_value = rules
    MockRuleSession.return_value = rule_session

    with patch.object(stale_rule_detector, "logger") as mock_logger:
        with patch("argparse.ArgumentParser.parse_args", return_value=type("Args", (), {"dry_run": True, "stale_days": 180})()):
            stale_rule_detector.main()
        log_msgs = " ".join(str(call) for call in mock_logger.info.call_args_list)
        assert "STALE MEMORY" in log_msgs
        assert "DEPRECATED MEMORY" in log_msgs
        assert "STALE RULE" in log_msgs
        assert "DEPRECATED RULE" in log_msgs 
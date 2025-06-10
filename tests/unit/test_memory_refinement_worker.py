import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from scripts import memory_refinement_worker

def make_node(id, namespace, content, meta=None):
    node = MagicMock()
    node.id = id
    node.namespace = namespace
    node.content = content
    node.meta = meta
    return node

@patch("scripts.memory_refinement_worker.MemorySessionLocal")
@patch("scripts.memory_refinement_worker.call_ollama")
def test_memory_refinement_dry_run(mock_ollama, MockSessionLocal):
    # Simulate LLM responses
    mock_ollama.side_effect = ["Short summary.", "Clarified content."]
    # Create test nodes: one long, one ambiguous, two similar
    nodes = [
        make_node("1", "ns", "x"*600),  # long
        make_node("2", "ns", "TBD: clarify this"),  # ambiguous
        make_node("3", "ns", "foo bar baz"),
        make_node("4", "ns", "foo bar baz!"),  # similar to id=3
    ]
    session = MagicMock()
    session.query.return_value.all.return_value = nodes
    MockSessionLocal.return_value = session

    with patch.object(memory_refinement_worker, "logger") as mock_logger:
        with patch("argparse.ArgumentParser.parse_args", return_value=type("Args", (), {"dry_run": True, "apply": False})()):
            memory_refinement_worker.main()
        log_msgs = " ".join(str(call) for call in mock_logger.info.call_args_list)
        assert "SUMMARY" in log_msgs
        assert "CLARIFY" in log_msgs
        assert "MERGE SUGGESTION" in log_msgs
        session.commit.assert_not_called() 
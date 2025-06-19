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
    # Simulate LLM responses: summary for long, clarification for ambiguous
    mock_ollama.side_effect = ["Short summary.", "Clarified content."]
    # Create test nodes: one long, one ambiguous, two unrelated
    long_content = "x" * 600  # triggers summary
    ambiguous_content = (
        "unclear: clarify this"  # triggers clarify, matches ambiguous phrase
    )
    unrelated_content_1 = "completely unrelated content 1"
    unrelated_content_2 = "completely unrelated content 2"
    nodes = [
        type(
            "Node",
            (),
            {"id": 1, "namespace": "ns", "content": long_content, "meta": ""},
        )(),
        type(
            "Node",
            (),
            {"id": 2, "namespace": "ns", "content": ambiguous_content, "meta": ""},
        )(),
        type(
            "Node",
            (),
            {"id": 3, "namespace": "ns", "content": unrelated_content_1, "meta": ""},
        )(),
        type(
            "Node",
            (),
            {"id": 4, "namespace": "ns", "content": unrelated_content_2, "meta": ""},
        )(),
    ]
    session = MockSessionLocal.return_value
    session.query.return_value.all.return_value = nodes
    session.commit = lambda: None
    with patch.object(memory_refinement_worker, "MERGE_SIMILARITY_THRESHOLD", 0.99):
        with patch.object(memory_refinement_worker, "logger") as mock_logger:
            with patch(
                "argparse.ArgumentParser.parse_args",
                return_value=type("Args", (), {"dry_run": True, "apply": False})(),
            ):
                memory_refinement_worker.main()
        log_msgs = " ".join(
            str(call) for call in mock_logger.info.call_args_list
        ).lower()
        if "clarify" not in log_msgs:
            print("Captured log messages:", log_msgs)
            print("LLM call args:", mock_ollama.call_args_list)
            print("Node contents:", [n.content for n in nodes])
        assert (
            "summary" in log_msgs
        ), "Expected '[SUMMARY]' log message for long content."
        assert (
            "clarify" in log_msgs
        ), "Expected '[CLARIFY]' log message for ambiguous content."
        assert (
            "merge suggestion" not in log_msgs
        ), "Did not expect '[MERGE SUGGESTION]' log message for unrelated nodes."

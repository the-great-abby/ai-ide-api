import numpy as np

def test_memory_node_fields(memory_node):
    node = memory_node("This is a test for embedding automation.")
    assert isinstance(node, dict)
    assert node["content"] == "This is a test for embedding automation."
    assert "embedding" not in node 
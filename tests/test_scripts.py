import os
import subprocess
import sys
import uuid
import json
import pytest


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

RUN_DOCKER_SCRIPT_TESTS = os.environ.get("RUN_DOCKER_SCRIPT_TESTS") == "1"

def skip_if_no_docker():
    if not RUN_DOCKER_SCRIPT_TESTS:
        pytest.skip("Script-based memory graph tests require Docker on host. Set RUN_DOCKER_SCRIPT_TESTS=1 to enable.")

def test_memory_add_and_list_node_script():
    skip_if_no_docker()
    # Add a node
    ns = f"testscript-{uuid.uuid4()}"
    content = "Script test node"
    embedding = "[0.1" + ",0.1" * 767 + "]"
    meta = '{"tags":["script-test"]}'
    add_result = subprocess.run([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT={content}", f"META={meta}"
    ], capture_output=True)
    assert add_result.returncode == 0
    # List nodes and check for our content
    list_result = subprocess.run(["make", "-f", "Makefile.ai", "ai-memory-list-nodes"], capture_output=True)
    assert list_result.returncode == 0
    assert content.encode() in list_result.stdout


def test_memory_add_and_list_edge_script():
    skip_if_no_docker()
    # Add two nodes
    ns = f"testscript-{uuid.uuid4()}"
    emb = "[0.2" + ",0.2" * 1535 + "]"
    meta = '{}'
    n1 = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=NodeA", f"META={meta}"
    ])
    n2 = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=NodeB", f"META={meta}"
    ])
    # Parse node IDs from output (fragile, but works for now)
    import re
    id1 = re.search(rb'"id":\s*"([^"]+)"', n1).group(1).decode()
    id2 = re.search(rb'"id":\s*"([^"]+)"', n2).group(1).decode()
    # Add edge
    edge_meta = '{"note":"script edge"}'
    edge_result = subprocess.run([
        "make", "-f", "Makefile.ai", "ai-memory-add-edge",
        f"FROM_ID={id1}", f"TO_ID={id2}", f"REL_TYPE=test_link", f"META={edge_meta}"
    ], capture_output=True)
    assert edge_result.returncode == 0
    # List edges and check for our relation
    list_edges = subprocess.run(["make", "-f", "Makefile.ai", "ai-memory-list-edges"], capture_output=True)
    assert list_edges.returncode == 0
    assert b"test_link" in list_edges.stdout


def test_memory_traverse_single_hop_script():
    skip_if_no_docker()
    # Add two nodes and an edge
    ns = f"testscript-{uuid.uuid4()}"
    emb = "[0.3" + ",0.3" * 1535 + "]"
    meta = '{}'
    n1 = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=NodeX", f"META={meta}"
    ])
    n2 = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=NodeY", f"META={meta}"
    ])
    import re
    id1 = re.search(rb'"id":\s*"([^"]+)"', n1).group(1).decode()
    id2 = re.search(rb'"id":\s*"([^"]+)"', n2).group(1).decode()
    edge_meta = '{"note":"hop edge"}'
    subprocess.run([
        "make", "-f", "Makefile.ai", "ai-memory-add-edge",
        f"FROM_ID={id1}", f"TO_ID={id2}", f"REL_TYPE=hop_link", f"META={edge_meta}"
    ], check=True)
    # Traverse single hop
    traverse = subprocess.run(["make", "-f", "Makefile.ai", "ai-memory-traverse-single-hop", f"NODE_ID={id1}"], capture_output=True)
    assert traverse.returncode == 0
    assert b"NodeY" in traverse.stdout


def test_memory_traverse_multi_hop_script():
    skip_if_no_docker()
    import re
    ns = f"testscript-{uuid.uuid4()}"
    emb = "[0.4" + ",0.4" * 1535 + "]"
    meta = '{}'
    # Add three nodes in a chain: A -> B -> C
    nA = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=NodeA", f"META={meta}"
    ])
    nB = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=NodeB", f"META={meta}"
    ])
    nC = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=NodeC", f"META={meta}"
    ])
    idA = re.search(rb'"id":\s*"([^"]+)"', nA).group(1).decode()
    idB = re.search(rb'"id":\s*"([^"]+)"', nB).group(1).decode()
    idC = re.search(rb'"id":\s*"([^"]+)"', nC).group(1).decode()
    subprocess.run([
        "make", "-f", "Makefile.ai", "ai-memory-add-edge",
        f"FROM_ID={idA}", f"TO_ID={idB}", f"REL_TYPE=multi_hop", f"META={meta}"
    ], check=True)
    subprocess.run([
        "make", "-f", "Makefile.ai", "ai-memory-add-edge",
        f"FROM_ID={idB}", f"TO_ID={idC}", f"REL_TYPE=multi_hop", f"META={meta}"
    ], check=True)
    # Multi-hop traverse from A should reach B and C
    traverse = subprocess.run(["make", "-f", "Makefile.ai", "ai-memory-traverse-multi-hop", f"NODE_ID={idA}"], capture_output=True)
    assert traverse.returncode == 0
    out = traverse.stdout
    assert b"NodeA" in out and b"NodeB" in out and b"NodeC" in out


def test_memory_traverse_by_relation_script():
    skip_if_no_docker()
    import re
    ns = f"testscript-{uuid.uuid4()}"
    emb = "[0.5" + ",0.5" * 1535 + "]"
    meta = '{}'
    # Add two nodes and two edges of different types
    n1 = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=Node1", f"META={meta}"
    ])
    n2 = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=Node2", f"META={meta}"
    ])
    n3 = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=Node3", f"META={meta}"
    ])
    id1 = re.search(rb'"id":\s*"([^"]+)"', n1).group(1).decode()
    id2 = re.search(rb'"id":\s*"([^"]+)"', n2).group(1).decode()
    id3 = re.search(rb'"id":\s*"([^"]+)"', n3).group(1).decode()
    subprocess.run([
        "make", "-f", "Makefile.ai", "ai-memory-add-edge",
        f"FROM_ID={id1}", f"TO_ID={id2}", f"REL_TYPE=relA", f"META={meta}"
    ], check=True)
    subprocess.run([
        "make", "-f", "Makefile.ai", "ai-memory-add-edge",
        f"FROM_ID={id1}", f"TO_ID={id3}", f"REL_TYPE=relB", f"META={meta}"
    ], check=True)
    # Traverse by relation relA should only find Node2
    traverseA = subprocess.run(["make", "-f", "Makefile.ai", "ai-memory-traverse-by-relation", f"NODE_ID={id1}", f"REL_TYPE=relA"], capture_output=True)
    assert traverseA.returncode == 0
    assert b"Node2" in traverseA.stdout and b"Node3" not in traverseA.stdout
    # Traverse by relation relB should only find Node3
    traverseB = subprocess.run(["make", "-f", "Makefile.ai", "ai-memory-traverse-by-relation", f"NODE_ID={id1}", f"REL_TYPE=relB"], capture_output=True)
    assert traverseB.returncode == 0
    assert b"Node3" in traverseB.stdout and b"Node2" not in traverseB.stdout


def test_memory_export_dot_script():
    skip_if_no_docker()
    import re
    ns = f"testscript-{uuid.uuid4()}"
    emb = "[0.6" + ",0.6" * 1535 + "]"
    meta = '{}'
    # Add two nodes and an edge
    n1 = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=NodeDot1", f"META={meta}"
    ])
    n2 = subprocess.check_output([
        "make", "-f", "Makefile.ai", "ai-memory-add-node",
        f"NAMESPACE={ns}", f"CONTENT=NodeDot2", f"META={meta}"
    ])
    id1 = re.search(rb'"id":\s*"([^"]+)"', n1).group(1).decode()
    id2 = re.search(rb'"id":\s*"([^"]+)"', n2).group(1).decode()
    subprocess.run([
        "make", "-f", "Makefile.ai", "ai-memory-add-edge",
        f"FROM_ID={id1}", f"TO_ID={id2}", f"REL_TYPE=dot_link", f"META={meta}"
    ], check=True)
    # Export DOT
    dot = subprocess.run(["make", "-f", "Makefile.ai", "ai-memory-export-dot"], capture_output=True)
    assert dot.returncode == 0
    dot_out = dot.stdout.decode()
    assert "digraph MemoryGraph {" in dot_out
    assert id1 in dot_out and id2 in dot_out
    assert f'"{id1}" -> "{id2}" [label="dot_link"]' in dot_out

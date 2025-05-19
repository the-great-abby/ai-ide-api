"""
Proactive Error Handling Module

Suggests fixes or next steps for errors by searching the memory graph for known solutions or related issues.
"""

from typing import List, Dict

def suggest_fixes_for_error(error_message: str, memory_nodes: List[Dict], memory_edges: List[Dict]) -> List[Dict]:
    """
    Suggest fixes for an error message by searching memory nodes for relevant solutions or related issues.
    Uses string/tag matching. Placeholder for semantic search.
    Returns a list of suggested nodes.
    """
    suggestions = []
    error_lower = error_message.lower()
    for node in memory_nodes:
        meta = node.get("meta", "{}")
        content = node.get("content", "")
        if any(tag in meta for tag in ["solution", "error", "troubleshooting"]):
            if error_lower in content.lower():
                suggestions.append(node)
    # TODO: Integrate semantic search using Ollama or embeddings
    return suggestions


def main():
    import argparse, json
    parser = argparse.ArgumentParser(description="Suggest fixes for an error message using the memory graph.")
    parser.add_argument("--error", required=True, help="Error message to search for")
    parser.add_argument("--nodes", required=True, help="Path to JSON file with memory nodes")
    parser.add_argument("--edges", required=False, help="Path to JSON file with memory edges")
    args = parser.parse_args()
    with open(args.nodes) as f:
        memory_nodes = json.load(f)
    memory_edges = []
    if args.edges:
        with open(args.edges) as f:
            memory_edges = json.load(f)
    suggestions = suggest_fixes_for_error(args.error, memory_nodes, memory_edges)
    if suggestions:
        print("Possible solutions found:")
        for s in suggestions:
            print("-", s.get("content", "<no content>"))
    else:
        print("No known solutions found. Consider adding this error to the memory graph.")

if __name__ == "__main__":
    main() 
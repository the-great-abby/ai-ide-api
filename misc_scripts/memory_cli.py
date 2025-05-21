#!/usr/bin/env python3
import argparse
import json
import sys
from memory_utils import (
    add_node, add_edge, list_nodes, list_edges,
    traverse_single_hop, traverse_multi_hop, traverse_by_relation,
    export_dot, delete_nodes
)

def main():
    parser = argparse.ArgumentParser(description="Memory Graph CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Add node command
    add_node_parser = subparsers.add_parser("add-node", help="Add a new node")
    add_node_parser.add_argument("namespace", help="Node namespace")
    add_node_parser.add_argument("content", help="Node content")
    add_node_parser.add_argument("--meta", help="Node metadata as JSON", default="{}")

    # Add edge command
    add_edge_parser = subparsers.add_parser("add-edge", help="Add a new edge")
    add_edge_parser.add_argument("from_id", help="Source node ID")
    add_edge_parser.add_argument("to_id", help="Target node ID")
    add_edge_parser.add_argument("relation_type", help="Type of relation")
    add_edge_parser.add_argument("--meta", help="Edge metadata as JSON", default="{}")

    # List nodes command
    subparsers.add_parser("list-nodes", help="List all nodes")

    # List edges command
    subparsers.add_parser("list-edges", help="List all edges")

    # Traverse commands
    traverse_parser = subparsers.add_parser("traverse", help="Traverse the graph")
    traverse_parser.add_argument("node_id", help="Starting node ID")
    traverse_parser.add_argument("--hops", type=int, help="Number of hops (default: 1)")
    traverse_parser.add_argument("--relation-type", help="Filter by relation type")

    # Export DOT command
    subparsers.add_parser("export-dot", help="Export graph in DOT format")

    # Delete nodes command
    delete_parser = subparsers.add_parser("delete-nodes", help="Delete nodes")
    delete_parser.add_argument("--namespace", help="Delete nodes in namespace")

    args = parser.parse_args()

    try:
        if args.command == "add-node":
            meta = json.loads(args.meta)
            result = add_node(args.namespace, args.content, meta)
            print(json.dumps(result, indent=2))

        elif args.command == "add-edge":
            meta = json.loads(args.meta)
            result = add_edge(args.from_id, args.to_id, args.relation_type, meta)
            print(json.dumps(result, indent=2))

        elif args.command == "list-nodes":
            result = list_nodes()
            print(json.dumps(result, indent=2))

        elif args.command == "list-edges":
            result = list_edges()
            print(json.dumps(result, indent=2))

        elif args.command == "traverse":
            if args.relation_type:
                result = traverse_by_relation(args.node_id, args.relation_type)
            elif args.hops and args.hops > 1:
                result = traverse_multi_hop(args.node_id, args.hops)
            else:
                result = traverse_single_hop(args.node_id)
            print(json.dumps(result, indent=2))

        elif args.command == "export-dot":
            result = export_dot()
            print(result)

        elif args.command == "delete-nodes":
            delete_nodes(args.namespace)
            print(f"Deleted nodes{f' in namespace {args.namespace}' if args.namespace else ''}")

        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 
#!/bin/bash
# Usage: ./memory_export_dot.sh > graph.dot
echo "digraph MemoryGraph {"
curl -s http://localhost:9103/memory/edges | jq -r '.[] | "\"\(.from_id)\" -> \"\(.to_id)\" [label=\"\(.relation_type)\"] ;"'
echo "}" 
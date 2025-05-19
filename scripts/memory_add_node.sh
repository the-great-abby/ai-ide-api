#!/bin/bash
# Usage: ./memory_add_node.sh "<namespace>" "<content>" "<meta_json>"
# Example: ./memory_add_node.sh notes "My note" '{"tags":["example"]}'

NAMESPACE="$1"
CONTENT="$2"
META="$3"

curl -X POST http://localhost:9103/memory/nodes \
  -H "Content-Type: application/json" \
  -d "{\"namespace\": \"$NAMESPACE\", \"content\": \"$CONTENT\", \"meta\": $META}" 
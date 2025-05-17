#!/bin/bash
# Usage: ./memory_add_node.sh "<namespace>" "<content>" "<embedding_json_array>" "<meta_json>"
# Example: ./memory_add_node.sh notes "My note" "[0.1,0.2,...]" '{"tags":["example"]}'

NAMESPACE="$1"
CONTENT="$2"
EMBEDDING="$3"
META="$4"

curl -X POST http://localhost:9103/memory/nodes \
  -H "Content-Type: application/json" \
  -d "{\"namespace\": \"$NAMESPACE\", \"content\": \"$CONTENT\", \"embedding\": $EMBEDDING, \"meta\": \"$META\"}" 
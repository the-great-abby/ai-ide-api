#!/bin/bash
# Usage: ./memory_add_edge.sh <from_id> <to_id> <relation_type> <meta_json>
# Example: ./memory_add_edge.sh NODE1_ID NODE2_ID related_to '{"note":"Example edge"}'

FROM_ID="$1"
TO_ID="$2"
RELATION_TYPE="$3"
META="$4"

curl -X POST http://localhost:9103/memory/edges \
  -H "Content-Type: application/json" \
  -d "{\"from_id\": \"$FROM_ID\", \"to_id\": \"$TO_ID\", \"relation_type\": \"$RELATION_TYPE\", \"meta\": \"$META\"}" 
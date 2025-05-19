#!/bin/bash
# Usage: ./memory_traverse_by_relation.sh <node_id> <relation_type>
NODE_ID="$1"
REL_TYPE="$2"
for to_id in $(curl -s "http://localhost:9103/memory/edges?from_id=$NODE_ID&relation_type=$REL_TYPE" | jq -r '.[].to_id'); do
  curl -s http://localhost:9103/memory/nodes | jq --arg id "$to_id" '.[] | select(.id == $id)'
done 
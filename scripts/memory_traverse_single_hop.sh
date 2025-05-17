#!/bin/bash
# Usage: ./memory_traverse_single_hop.sh <node_id>
NODE_ID="$1"
for to_id in $(curl -s "http://localhost:9103/memory/edges?from_id=$NODE_ID" | jq -r '.[].to_id'); do
  curl -s http://localhost:9103/memory/nodes | jq --arg id "$to_id" '.[] | select(.id == $id)'
done 
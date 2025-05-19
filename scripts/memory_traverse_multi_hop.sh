#!/bin/bash
# Usage: ./memory_traverse_multi_hop.sh <start_node_id>
START_NODE="$1"
declare -A visited
traverse() {
  local node_id="$1"
  if [[ -n "${visited[$node_id]}" ]]; then return; fi
  visited[$node_id]=1
  echo "Node: $node_id"
  curl -s http://localhost:9103/memory/nodes | jq --arg id "$node_id" '.[] | select(.id == $id)'
  for to_id in $(curl -s "http://localhost:9103/memory/edges?from_id=$node_id" | jq -r '.[].to_id'); do
    traverse "$to_id"
  done
}
traverse "$START_NODE" 
#!/bin/bash
# Usage: ./memory_list_nodes.sh
curl http://localhost:9103/memory/nodes | jq . 
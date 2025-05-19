#!/bin/bash
# Usage: ./memory_list_edges.sh
curl http://localhost:9103/memory/edges | jq . 
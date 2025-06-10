#!/bin/bash
# 10_install_extensions_in_all_dbs.sh
# Arrr! Patch McDebug says: This script ensures all our Postgres extensions be installed in every port and cove!

set -e

# Wait for rulesdb and memorydb to exist
for db in rulesdb memorydb; do
  echo "[PIRATE] Waitin' for $db to be ready..."
  until psql -U "$POSTGRES_USER" -d postgres -c "\l" | grep -q "$db"; do
    sleep 1
  done
done

# Install extensions in rulesdb
psql -U "$POSTGRES_USER" -d rulesdb -f /docker-entrypoint-initdb.d/01_create_rulesdb_extensions.sql
# Install extensions in memorydb
psql -U "$POSTGRES_USER" -d memorydb -f /docker-entrypoint-initdb.d/02_create_memorydb_extensions.sql

echo "[PIRATE] All extensions be installed! Yo ho ho!" 
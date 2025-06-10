#!/bin/bash
# entrypoint-pirate.sh
# Arrr! Patch McDebug's custom entrypoint for Postgres, so no extension be left behind!

set -e

# Start Postgres in the background
/docker-entrypoint.sh postgres &
PG_PID=$!

# Wait for Postgres to be ready
until pg_isready -U "$POSTGRES_USER"; do
  echo "[PIRATE] Waitin' for Postgres to be ready..."
  sleep 1
done

# Create databases if they don't exist
for db in rulesdb memorydb; do
  if ! psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$db"; then
    echo "[PIRATE] Creating $db..."
    createdb -U "$POSTGRES_USER" "$db"
  fi
done

# Install extensions with retry logic
for db in rulesdb memorydb; do
  for ext in vector pg_trgm; do
    tries=0
    until psql -U "$POSTGRES_USER" -d "$db" -c "CREATE EXTENSION IF NOT EXISTS $ext;"; do
      tries=$((tries+1))
      if [ $tries -gt 10 ]; then
        echo "[PIRATE] Failed to install $ext in $db after 10 tries! Abandon ship!"
        exit 1
      fi
      echo "[PIRATE] Try $tries: Waitin' to install $ext in $db..."
      sleep 2
    done
    echo "[PIRATE] $ext be installed in $db!"
  done
done

# Bring Postgres to the foreground
wait $PG_PID 
#!/bin/bash
set -e

psql -h rules-postgres -U postgres -d rulesdb -f /data/sqlite_export/schema.patched.sql

for f in /data/sqlite_export/*.csv; do
  if [ -s "$f" ]; then
    tbl=$(basename "$f" .csv)
    echo "Importing $f into $tbl..."
    psql -h rules-postgres -U postgres -d rulesdb -c "\\copy \"$tbl\" FROM '/data/sqlite_export/$tbl.csv' WITH CSV HEADER"
  else
    echo "Skipping empty CSV: $f"
  fi
done 
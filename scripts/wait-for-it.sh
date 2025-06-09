#!/usr/bin/env python3
import os
import sys
import time
import psycopg2

host = sys.argv[1]
cmd = sys.argv[2:]

user = os.environ.get("POSTGRES_USER", "postgres")
password = os.environ.get("POSTGRES_PASSWORD", "postgres")
db = os.environ.get("POSTGRES_DB", "postgres")
port = int(os.environ.get("POSTGRES_PORT", 5432))

while True:
    try:
        conn = psycopg2.connect(host=host, user=user, password=password, dbname=db, port=port)
        conn.close()
        break
    except Exception as e:
        print(f"Postgres is unavailable - sleeping ({e})", file=sys.stderr)
        time.sleep(1)

print("Postgres is up - executing command", file=sys.stderr)
os.execvp(cmd[0], cmd) 
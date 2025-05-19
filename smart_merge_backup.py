#!/usr/bin/env python3
import os
import sys
import subprocess
import psycopg2
import time
import uuid
import argparse

# --- Configurable main tables and their upsert SQL templates ---
# (table_name: (column_list, upsert_sql_template))
TABLES = {
    'memory_edges': (
        ['id', 'from_id', 'to_id', 'relation_type', 'meta', 'created_at'],
        '''INSERT INTO memory_edges (id, from_id, to_id, relation_type, meta, created_at)
SELECT id, from_id, to_id, relation_type, meta, created_at FROM temp_schema.memory_edges
ON CONFLICT (id) DO UPDATE SET
  from_id = EXCLUDED.from_id,
  to_id = EXCLUDED.to_id,
  relation_type = EXCLUDED.relation_type,
  meta = EXCLUDED.meta,
  created_at = EXCLUDED.created_at;'''),
    'memory_vectors': (
        ['id', 'vector', 'namespace', 'reference_id', 'created_at'],
        '''INSERT INTO memory_vectors (id, vector, namespace, reference_id, created_at)
SELECT id, vector, namespace, reference_id, created_at FROM temp_schema.memory_vectors
ON CONFLICT (id) DO UPDATE SET
  vector = EXCLUDED.vector,
  namespace = EXCLUDED.namespace,
  reference_id = EXCLUDED.reference_id,
  created_at = EXCLUDED.created_at;'''),
    'api_error_logs': (
        ['id', 'timestamp', 'path', 'method', 'status_code', 'message', 'stack_trace', 'user_id'],
        '''INSERT INTO api_error_logs (id, "timestamp", path, method, status_code, message, stack_trace, user_id)
SELECT id, "timestamp", path, method, status_code, message, stack_trace, user_id FROM temp_schema.api_error_logs
ON CONFLICT (id) DO UPDATE SET
  "timestamp" = EXCLUDED."timestamp",
  path = EXCLUDED.path,
  method = EXCLUDED.method,
  status_code = EXCLUDED.status_code,
  message = EXCLUDED.message,
  stack_trace = EXCLUDED.stack_trace,
  user_id = EXCLUDED.user_id;'''),
    'project_memberships': (
        ['id', 'project_id', 'user_id', 'role', 'created_at'],
        '''INSERT INTO project_memberships (id, project_id, user_id, role, created_at)
SELECT id, project_id, user_id, role, created_at FROM temp_schema.project_memberships
ON CONFLICT (id) DO UPDATE SET
  project_id = EXCLUDED.project_id,
  user_id = EXCLUDED.user_id,
  role = EXCLUDED.role,
  created_at = EXCLUDED.created_at;'''),
    'projects': (
        ['id', 'name', 'description', 'created_at'],
        '''INSERT INTO projects (id, name, description, created_at)
SELECT id, name, description, created_at FROM temp_schema.projects
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  created_at = EXCLUDED.created_at;'''),
    'api_access_tokens': (
        ['id', 'token', 'created_at', 'created_by', 'description', 'active'],
        '''INSERT INTO api_access_tokens (id, token, created_at, created_by, description, active)
SELECT id, token, created_at, created_by, description, active FROM temp_schema.api_access_tokens
ON CONFLICT (id) DO UPDATE SET
  token = EXCLUDED.token,
  created_at = EXCLUDED.created_at,
  created_by = EXCLUDED.created_by,
  description = EXCLUDED.description,
  active = EXCLUDED.active;'''),
    'rules': (
        ['id', 'rule_type', 'description', 'diff', 'status', 'submitted_by', 'added_by', 'project', 'timestamp', 'version', 'categories', 'tags', 'examples', 'applies_to', 'applies_to_rationale', 'user_story'],
        '''INSERT INTO rules (id, rule_type, description, diff, status, submitted_by, added_by, project, "timestamp", version, categories, tags, examples, applies_to, applies_to_rationale, user_story)
SELECT id, rule_type, description, diff, status, submitted_by, added_by, project, "timestamp", version, categories, tags, examples, applies_to, applies_to_rationale, user_story FROM temp_schema.rules
ON CONFLICT (id) DO UPDATE SET
  rule_type = EXCLUDED.rule_type,
  description = EXCLUDED.description,
  diff = EXCLUDED.diff,
  status = EXCLUDED.status,
  submitted_by = EXCLUDED.submitted_by,
  added_by = EXCLUDED.added_by,
  project = EXCLUDED.project,
  "timestamp" = EXCLUDED."timestamp",
  version = EXCLUDED.version,
  categories = EXCLUDED.categories,
  tags = EXCLUDED.tags,
  examples = EXCLUDED.examples,
  applies_to = EXCLUDED.applies_to,
  applies_to_rationale = EXCLUDED.applies_to_rationale,
  user_story = EXCLUDED.user_story;'''),
    'rule_versions': (
        ['id', 'rule_id', 'version', 'rule_type', 'description', 'diff', 'status', 'submitted_by', 'added_by', 'project', 'timestamp', 'categories', 'tags', 'examples', 'applies_to', 'applies_to_rationale', 'user_story'],
        '''INSERT INTO rule_versions (id, rule_id, version, rule_type, description, diff, status, submitted_by, added_by, project, "timestamp", categories, tags, examples, applies_to, applies_to_rationale, user_story)
SELECT id, rule_id, version, rule_type, description, diff, status, submitted_by, added_by, project, "timestamp", categories, tags, examples, applies_to, applies_to_rationale, user_story FROM temp_schema.rule_versions
ON CONFLICT (id) DO UPDATE SET
  rule_id = EXCLUDED.rule_id,
  version = EXCLUDED.version,
  rule_type = EXCLUDED.rule_type,
  description = EXCLUDED.description,
  diff = EXCLUDED.diff,
  status = EXCLUDED.status,
  submitted_by = EXCLUDED.submitted_by,
  added_by = EXCLUDED.added_by,
  project = EXCLUDED.project,
  "timestamp" = EXCLUDED."timestamp",
  categories = EXCLUDED.categories,
  tags = EXCLUDED.tags,
  examples = EXCLUDED.examples,
  applies_to = EXCLUDED.applies_to,
  applies_to_rationale = EXCLUDED.applies_to_rationale,
  user_story = EXCLUDED.user_story;'''),
    'enhancements': (
        ['id', 'description', 'suggested_by', 'page', 'tags', 'categories', 'timestamp', 'status', 'proposal_id', 'project', 'examples', 'applies_to', 'applies_to_rationale', 'user_story', 'diff'],
        '''INSERT INTO enhancements (id, description, suggested_by, page, tags, categories, "timestamp", status, proposal_id, project, examples, applies_to, applies_to_rationale, user_story, diff)
SELECT id, description, suggested_by, page, tags, categories, "timestamp", status, proposal_id, project, examples, applies_to, applies_to_rationale, user_story, diff FROM temp_schema.enhancements
ON CONFLICT (id) DO UPDATE SET
  description = EXCLUDED.description,
  suggested_by = EXCLUDED.suggested_by,
  page = EXCLUDED.page,
  tags = EXCLUDED.tags,
  categories = EXCLUDED.categories,
  "timestamp" = EXCLUDED."timestamp",
  status = EXCLUDED.status,
  proposal_id = EXCLUDED.proposal_id,
  project = EXCLUDED.project,
  examples = EXCLUDED.examples,
  applies_to = EXCLUDED.applies_to,
  applies_to_rationale = EXCLUDED.applies_to_rationale,
  user_story = EXCLUDED.user_story,
  diff = EXCLUDED.diff;'''),
    'feedback': (
        ['id', 'rule_id', 'project', 'feedback_type', 'comment', 'submitted_by', 'timestamp'],
        '''INSERT INTO feedback (id, rule_id, project, feedback_type, comment, submitted_by, "timestamp")
SELECT id, rule_id, project, feedback_type, comment, submitted_by, "timestamp" FROM temp_schema.feedback
ON CONFLICT (id) DO UPDATE SET
  rule_id = EXCLUDED.rule_id,
  project = EXCLUDED.project,
  feedback_type = EXCLUDED.feedback_type,
  comment = EXCLUDED.comment,
  submitted_by = EXCLUDED.submitted_by,
  "timestamp" = EXCLUDED."timestamp";'''),
    'proposals': (
        ['id', 'rule_type', 'description', 'diff', 'status', 'submitted_by', 'project', 'timestamp', 'version', 'categories', 'tags', 'rule_id'],
        '''INSERT INTO proposals (id, rule_type, description, diff, status, submitted_by, project, "timestamp", version, categories, tags, rule_id)
SELECT id, rule_type, description, diff, status, submitted_by, project, "timestamp", version, categories, tags, rule_id FROM temp_schema.proposals
ON CONFLICT (id) DO UPDATE SET
  rule_type = EXCLUDED.rule_type,
  description = EXCLUDED.description,
  diff = EXCLUDED.diff,
  status = EXCLUDED.status,
  submitted_by = EXCLUDED.submitted_by,
  project = EXCLUDED.project,
  "timestamp" = EXCLUDED."timestamp",
  version = EXCLUDED.version,
  categories = EXCLUDED.categories,
  tags = EXCLUDED.tags,
  rule_id = EXCLUDED.rule_id;'''),
    'bug_reports': (
        ['id', 'description', 'reporter', 'page', 'timestamp', 'user_story'],
        '''INSERT INTO bug_reports (id, description, reporter, page, "timestamp", user_story)
SELECT id, description, reporter, page, "timestamp", user_story FROM temp_schema.bug_reports
ON CONFLICT (id) DO UPDATE SET
  description = EXCLUDED.description,
  reporter = EXCLUDED.reporter,
  page = EXCLUDED.page,
  "timestamp" = EXCLUDED."timestamp",
  user_story = EXCLUDED.user_story;'''),
    'rule_proposal_feedback': (
        ['id', 'rule_proposal_id', 'user_id', 'feedback_type', 'comments', 'created_at'],
        '''INSERT INTO rule_proposal_feedback (id, rule_proposal_id, user_id, feedback_type, comments, created_at)
SELECT id, rule_proposal_id, user_id, feedback_type, comments, created_at FROM temp_schema.rule_proposal_feedback
ON CONFLICT (id) DO UPDATE SET
  rule_proposal_id = EXCLUDED.rule_proposal_id,
  user_id = EXCLUDED.user_id,
  feedback_type = EXCLUDED.feedback_type,
  comments = EXCLUDED.comments,
  created_at = EXCLUDED.created_at;'''),
}

# --- Utility functions ---
def log(msg):
    print(f"[merge-backup] {msg}", flush=True)

def run(cmd, check=True):
    log(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        log(f"Command failed: {cmd}")
        sys.exit(1)
    return result.returncode

def get_env(var, default=None, required=False):
    val = os.environ.get(var, default)
    if required and not val:
        log(f"Missing required environment variable: {var}")
        sys.exit(1)
    return val

def get_temp_db_name():
    return f"temp_restore_db_{uuid.uuid4().hex[:8]}"

def get_present_tables(pguser, pghost, pgport, temp_db):
    import psycopg2
    conn = psycopg2.connect(dbname=temp_db, user=pguser, host=pghost, port=pgport)
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return set(tables)

def detect_database_from_filename(filename):
    fname = os.path.basename(filename).lower()
    if 'memorydb' in fname:
        return 'memorydb'
    if 'rulesdb' in fname:
        return 'rulesdb'
    return None

def table_has_columns(conn, table, columns):
    cur = conn.cursor()
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table,))
    existing = set(row[0] for row in cur.fetchall())
    cur.close()
    return all(col in existing for col in columns)

def table_exists(conn, table):
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE LOWER(table_name) = LOWER(%s)
              AND table_schema = 'public'
              AND table_type = 'BASE TABLE'
        )
    """, (table,))
    exists = cur.fetchone()[0]
    cur.close()
    return exists

def foreign_table_exists(conn, schema, table):
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = %s AND LOWER(table_name) = LOWER(%s)
        )
    """, (schema, table))
    exists = cur.fetchone()[0]
    cur.close()
    return exists

def main():
    parser = argparse.ArgumentParser(description="Smart merge backup script for Postgres.")
    parser.add_argument("backup_sql", help="Path to backup .sql file")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without making changes")
    args = parser.parse_args()

    # DB connection info from env
    pguser = get_env("PGUSER", required=True)
    pgpassword = get_env("PGPASSWORD", required=True)
    pghost = get_env("PGHOST", required=True)
    pgport = get_env("PGPORT", required=True)
    livedb = os.environ.get("PGDATABASE")
    if not livedb:
        livedb = detect_database_from_filename(args.backup_sql)
        if livedb:
            log(f"Auto-detected PGDATABASE as '{livedb}' from filename.")
        else:
            log("Missing required environment variable: PGDATABASE and could not auto-detect from filename.")
            sys.exit(1)
    else:
        log(f"Using PGDATABASE from environment: {livedb}")
    os.environ["PGPASSWORD"] = pgpassword  # for subprocess

    temp_db = get_temp_db_name()
    log(f"Creating temp DB: {temp_db}")
    if not args.dry_run:
        run(f'createdb -U {pguser} -h {pghost} -p {pgport} {temp_db}')
        run(f'psql -U {pguser} -h {pghost} -p {pgport} -d {temp_db} -f "{args.backup_sql}"')

    log("Detecting tables in temp DB...")
    present_tables = get_present_tables(pguser, pghost, pgport, temp_db)
    log(f"Tables found: {', '.join(sorted(present_tables))}")

    log("Setting up postgres_fdw in live DB...")
    # Drop temp_schema if it exists, but ignore errors if it does not
    drop_schema_sql = "DROP SCHEMA IF EXISTS temp_schema CASCADE;"
    if not args.dry_run:
        try:
            run(f'psql -U {pguser} -h {pghost} -p {pgport} -d {livedb} -c "{drop_schema_sql}"', check=False)
        except Exception:
            pass  # Ignore errors
    else:
        log("[DRY RUN] Would drop temp_schema if exists.")

    # Try to import each safe table individually, skipping those that fail
    safe_tables = [
        'memory_edges', 'memory_vectors', 'api_error_logs', 'project_memberships', 'projects',
        'api_access_tokens', 'feedback', 'bug_reports', 'rule_proposal_feedback'
    ]
    fdw_cmds = [
        f'CREATE EXTENSION IF NOT EXISTS postgres_fdw;',
        f'DROP SERVER IF EXISTS temp_restore_server CASCADE;',
        f"CREATE SERVER temp_restore_server FOREIGN DATA WRAPPER postgres_fdw OPTIONS (host '{pghost}', dbname '{temp_db}', port '{pgport}');",
        f"CREATE USER MAPPING FOR CURRENT_USER SERVER temp_restore_server OPTIONS (user '{pguser}', password '{pgpassword}');",
        f'CREATE SCHEMA IF NOT EXISTS temp_schema;'
    ]
    for cmd in fdw_cmds:
        if not args.dry_run:
            log(f"Running FDW setup command: {cmd}")
            run(f'psql -U {pguser} -h {pghost} -p {pgport} -d {livedb} -c "{cmd}"', check=False)
        else:
            log(f"[DRY RUN] Would run FDW setup command: {cmd}")

    # Import each table individually, skipping on error
    for table in safe_tables:
        import_cmd = f'IMPORT FOREIGN SCHEMA public LIMIT TO ({table}) FROM SERVER temp_restore_server INTO temp_schema;'
        if not args.dry_run:
            log(f"Importing table via FDW: {table}")
            rc = run(f'psql -U {pguser} -h {pghost} -p {pgport} -d {livedb} -c "{import_cmd}"', check=False)
            if rc != 0:
                log(f"Skipping table {table} due to FDW import error.")
        else:
            log(f"[DRY RUN] Would import table via FDW: {table}")

    # Connect to live DB for column checks
    live_conn = psycopg2.connect(dbname=livedb, user=pguser, host=pghost, port=pgport)

    # Connect to temp DB for foreign table checks
    temp_conn = psycopg2.connect(dbname=temp_db, user=pguser, host=pghost, port=pgport)

    for table, (columns, upsert_sql) in TABLES.items():
        if table in present_tables:
            exists = table_exists(live_conn, table)
            log(f"Live DB table existence for '{table}': {exists}")
            if not exists:
                log(f"Skipping upsert for {table}: table does not exist in live DB.")
                continue
            if not table_has_columns(live_conn, table, columns):
                log(f"Skipping upsert for {table}: columns do not match live DB schema.")
                continue
            if not foreign_table_exists(temp_conn, 'temp_schema', table):
                log(f"Skipping upsert for {table}: foreign table temp_schema.{table} does not exist.")
                continue
            log(f"Upserting table: {table}")
            if args.dry_run:
                log(f"[DRY RUN] Would run upsert for {table}:")
                log(upsert_sql)
            else:
                run(f'psql -U {pguser} -h {pghost} -p {pgport} -d {livedb} -c "{upsert_sql}"')
        else:
            log(f"Table {table} not present in backup, skipping.")

    live_conn.close()
    temp_conn.close()

    log("Cleaning up: dropping temp DB and FDW objects...")
    cleanup_sql = "DROP SCHEMA IF EXISTS temp_schema CASCADE; DROP SERVER IF EXISTS temp_restore_server CASCADE;"
    if not args.dry_run:
        run(f'psql -U {pguser} -h {pghost} -p {pgport} -d {livedb} -c "{cleanup_sql}"')
        run(f'dropdb -U {pguser} -h {pghost} -p {pgport} {temp_db}')
    else:
        log(f"[DRY RUN] Would drop temp DB {temp_db} and cleanup FDW objects.")

    log("Merge complete!")

if __name__ == "__main__":
    main() 
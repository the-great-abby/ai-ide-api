import os
import sqlite3

BACKUP_DB = "rules.db.bak"
NEW_DB = "rules.db"


def copy_table(src_conn, dst_conn, table, columns, extra_dst_columns=None):
    src_cols = ", ".join([col for col in columns if col != "rule_id"])
    dst_cols = ", ".join(columns)
    placeholders = ", ".join(["?" for _ in columns])
    cursor = src_conn.cursor()
    try:
        cursor.execute(f"SELECT {src_cols} FROM {table}")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Skipping {table}: {e}")
        return 0
    dst_cursor = dst_conn.cursor()
    count = 0
    for row in rows:
        row = list(row)
        # Insert NULL for rule_id if needed
        if "rule_id" in columns:
            idx = columns.index("rule_id")
            row.insert(idx, None)
        try:
            dst_cursor.execute(
                f"INSERT INTO {table} ({dst_cols}) VALUES ({placeholders})", row
            )
            count += 1
        except Exception as e:
            print(f"Error inserting into {table}: {e}")
    dst_conn.commit()
    return count


def main():
    if not os.path.exists(BACKUP_DB):
        print(f"Backup DB {BACKUP_DB} not found.")
        return
    if not os.path.exists(NEW_DB):
        print(f"New DB {NEW_DB} not found.")
        return
    src_conn = sqlite3.connect(BACKUP_DB)
    dst_conn = sqlite3.connect(NEW_DB)

    tables = {
        "proposals": [
            "id",
            "rule_id",
            "rule_type",
            "description",
            "diff",
            "status",
            "submitted_by",
            "project",
            "timestamp",
            "version",
            "categories",
            "tags",
        ],
        "rules": [
            "id",
            "rule_type",
            "description",
            "diff",
            "status",
            "submitted_by",
            "added_by",
            "project",
            "timestamp",
            "version",
            "categories",
            "tags",
        ],
        "enhancements": [
            "id",
            "description",
            "suggested_by",
            "page",
            "tags",
            "categories",
            "timestamp",
            "status",
            "proposal_id",
        ],
        "feedback": [
            "id",
            "rule_id",
            "project",
            "feedback_type",
            "comment",
            "submitted_by",
            "timestamp",
        ],
        "bug_reports": ["id", "description", "reporter", "page", "timestamp"],
        "rule_versions": [
            "id",
            "rule_id",
            "version",
            "rule_type",
            "description",
            "diff",
            "status",
            "submitted_by",
            "added_by",
            "project",
            "timestamp",
            "categories",
            "tags",
        ],
    }
    for table, columns in tables.items():
        count = copy_table(src_conn, dst_conn, table, columns)
        print(f"Imported {count} rows into {table}.")
    src_conn.close()
    dst_conn.close()
    print("Import complete.")


if __name__ == "__main__":
    main()

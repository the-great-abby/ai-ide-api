import sqlite3
import requests

API_URL = "http://localhost:8000/approve-rule-change/{}"
DB_PATH = "rules.db"

def get_pending_proposal_ids(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM proposals WHERE status = 'pending';")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids

def approve_proposal(proposal_id):
    url = API_URL.format(proposal_id)
    try:
        response = requests.post(url)
        if response.status_code == 200:
            print(f"Approved: {proposal_id}")
        else:
            print(f"Failed to approve {proposal_id}: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error approving {proposal_id}: {e}")

def main():
    ids = get_pending_proposal_ids(DB_PATH)
    if not ids:
        print("No pending proposals found.")
        return
    for proposal_id in ids:
        approve_proposal(proposal_id)

if __name__ == "__main__":
    main() 
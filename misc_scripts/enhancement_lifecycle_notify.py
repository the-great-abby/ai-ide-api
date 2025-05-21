import requests
from datetime import datetime, timedelta
import os

API_BASE = os.environ.get("API_BASE", "http://api:8000")
ENHANCEMENTS_URL = f"{API_BASE}/enhancements"
STALE_DAYS = 14

def fetch_enhancements():
    resp = requests.get(ENHANCEMENTS_URL)
    resp.raise_for_status()
    return resp.json()

def find_stale(enhancements):
    now = datetime.utcnow()
    stale = []
    for enh in enhancements:
        # Assume 'timestamp' is ISO format and 'status' is present
        last_update = datetime.fromisoformat(enh['timestamp'])
        if enh.get('status', 'open') == 'open' and (now - last_update).days > STALE_DAYS:
            stale.append(enh)
    return stale

def notify_stale(stale_enhancements):
    for enh in stale_enhancements:
        print(f"[STALE] Enhancement {enh['id']} is stale: {enh['description']}")
        # Here you could add Slack/email/GitHub notification logic

if __name__ == "__main__":
    enhancements = fetch_enhancements()
    stale = find_stale(enhancements)
    if not stale:
        print("No stale enhancements found.")
    else:
        notify_stale(stale) 
import sys
import requests
import json

API_URL = "http://localhost:9103/review-code-files"
PROPOSE_URL = "http://localhost:9103/propose-rule-change"

propose = False
files = []
for arg in sys.argv[1:]:
    if arg == "--propose":
        propose = True
    else:
        files.append(arg)

if not files:
    print("Usage: python scripts/review_multiple_files.py file1.py file2.py [--propose]")
    sys.exit(1)

file_objs = [("files", open(f, "rb")) for f in files]
try:
    response = requests.post(API_URL, files=file_objs)
    response.raise_for_status()
    feedback = response.json()
    print(json.dumps(feedback, indent=2))

    if propose:
        # Collect unique rule_types and submit proposals
        seen = set()
        for file_feedback in feedback.values():
            for suggestion in file_feedback:
                rule_type = suggestion.get("rule_type")
                desc = suggestion.get("description")
                diff = suggestion.get("diff")
                if rule_type and (rule_type, desc) not in seen:
                    seen.add((rule_type, desc))
                    proposal = {
                        "rule_type": rule_type,
                        "description": desc,
                        "diff": diff,
                        "submitted_by": "auto-proposer",
                        "categories": ["auto"],
                        "tags": [rule_type],
                        "project": "ai-ide-api"
                    }
                    resp = requests.post(PROPOSE_URL, json=proposal)
                    if resp.ok:
                        print(f"Proposed rule: {rule_type} - {desc[:60]}...")
                    else:
                        print(f"Failed to propose rule: {rule_type}", resp.text)
finally:
    for _, f in file_objs:
        f.close() 
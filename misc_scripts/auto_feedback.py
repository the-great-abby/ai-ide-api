import requests
import os
import json
import subprocess
import sys

# Determine API base URL based on environment

def get_default_api_base():
    if os.environ.get("RUNNING_IN_DOCKER") == "1":
        return "http://api:8000"
    return "http://localhost:9103"

def get_api_base():
    return os.environ.get("API_BASE", get_default_api_base())

API_BASE = os.environ.get("API_BASE", get_default_api_base())
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q6_K")


def get_pending_proposals():
    resp = requests.get(f"{get_api_base()}/pending-rule-changes")
    resp.raise_for_status()
    return resp.json()


def rule_based_feedback(proposal):
    desc = proposal.get("description", "").lower()
    # Example: auto-accept if description contains 'format' or 'typo'
    if "format" in desc:
        return "accept", "Auto-accepted: formatting rule"
    if "typo" in desc:
        return "accept", "Auto-accepted: typo fix"
    # Add more rules as needed
    return None, None


def llm_feedback(proposal):
    import io
    import json

    prompt = (
        """
Given the following rule proposal, suggest feedback (accept, reject, needs_changes) and a brief comment as JSON: {"feedback_type": "accept|reject|needs_changes", "comments": "..."}
"""
        + json.dumps(proposal, indent=2)
    )
    payload = json.dumps({"model": MODEL, "prompt": prompt})
    resp = requests.post(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        timeout=120,
        stream=True,
    )
    resp.raise_for_status()

    # Collect all 'response' fields from the stream
    response_text = ""
    for line in resp.iter_lines():
        if not line:
            continue
        try:
            data = json.loads(line.decode("utf-8"))
            response_text += data.get("response", "")
            if data.get("done", False):
                break
        except Exception as e:
            continue

    # Try to parse JSON from LLM output
    try:
        feedback = json.loads(response_text[response_text.find("{"):response_text.rfind("}")+1])
        return feedback.get("feedback_type", "needs_changes"), feedback.get("comments", response_text)
    except Exception:
        # Fallback: look for keywords
        if "accept" in response_text.lower():
            return "accept", response_text
        elif "reject" in response_text.lower():
            return "reject", response_text
        elif "needs_changes" in response_text.lower():
            return "needs_changes", response_text
        return "needs_changes", "Unclear, needs human review: " + response_text


def submit_feedback(proposal_id, feedback_type, comments):
    feedback = {"feedback_type": feedback_type, "comments": comments}
    resp = requests.post(f"{get_api_base()}/api/rule_proposals/{proposal_id}/feedback", json=feedback)
    print(f"Submitted feedback for {proposal_id}: {feedback_type} ({comments[:60]})")
    return resp


def main():
    # Check for input file argument if present
    if len(sys.argv) > 1 and sys.argv[0].endswith('auto_feedback.py'):
        input_file = sys.argv[1]
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' does not exist.")
            sys.exit(1)
    try:
        proposals = get_pending_proposals()
    except Exception as e:
        print(f"Error fetching proposals: {e}")
        sys.exit(1)
    if not proposals:
        print("No pending proposals found.")
        return
    for proposal in proposals:
        feedback_type, comments = rule_based_feedback(proposal)
        if not feedback_type:
            feedback_type, comments = llm_feedback(proposal)
        try:
            submit_feedback(proposal["id"], feedback_type, comments)
        except Exception as e:
            print(f"Error submitting feedback: {e}")
            sys.exit(1)
        print(f"AI suggested: {feedback_type} - {comments}\n{'-'*40}")

if __name__ == "__main__":
    main() 
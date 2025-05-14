import requests
import os
import json

# Determine API base URL based on environment

def get_default_api_base():
    if os.environ.get("RUNNING_IN_DOCKER") == "1":
        return "http://api:8000"
    return "http://localhost:9103"

API_BASE = os.environ.get("API_BASE", get_default_api_base())
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3")


def get_pending_proposals():
    resp = requests.get(f"{API_BASE}/pending-rule-changes")
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
    prompt = (
        """
Given the following rule proposal, suggest feedback (accept, reject, needs_changes) and a brief comment as JSON: {"feedback_type": "accept|reject|needs_changes", "comments": "..."}
"""
        + json.dumps(proposal, indent=2)
    )
    resp = requests.post(OLLAMA_URL, json={"model": MODEL, "prompt": prompt, "stream": False}, timeout=120)
    resp.raise_for_status()
    result = resp.json().get("response", "")
    # Try to parse JSON from LLM output
    try:
        feedback = json.loads(result[result.find("{"):result.rfind("}")+1])
        return feedback.get("feedback_type", "needs_changes"), feedback.get("comments", result)
    except Exception:
        # Fallback: look for keywords
        if "accept" in result.lower():
            return "accept", result
        elif "reject" in result.lower():
            return "reject", result
        elif "needs_changes" in result.lower():
            return "needs_changes", result
        return "needs_changes", "Unclear, needs human review: " + result


def submit_feedback(proposal_id, feedback_type, comments):
    feedback = {"feedback_type": feedback_type, "comments": comments}
    resp = requests.post(f"{API_BASE}/api/rule_proposals/{proposal_id}/feedback", json=feedback)
    print(f"Submitted feedback for {proposal_id}: {feedback_type} ({comments[:60]})")
    return resp


def main():
    proposals = get_pending_proposals()
    if not proposals:
        print("No pending proposals found.")
        return
    for proposal in proposals:
        feedback_type, comments = rule_based_feedback(proposal)
        if not feedback_type:
            feedback_type, comments = llm_feedback(proposal)
        submit_feedback(proposal["id"], feedback_type, comments)
        print(f"AI suggested: {feedback_type} - {comments}\n{'-'*40}")

if __name__ == "__main__":
    main() 
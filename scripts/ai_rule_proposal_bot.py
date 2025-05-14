import os
import glob
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
API_URL = "http://localhost:9103/propose-rule-change"
MODEL = "llama3"

# 1. Scan codebase for repeated patterns (simple example: direct SQL queries)
def scan_codebase_for_patterns():
    sql_patterns = []
    for pyfile in glob.glob("**/*.py", recursive=True):
        with open(pyfile, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if "SELECT" in line or "INSERT" in line or "UPDATE" in line:
                    sql_patterns.append({
                        "file": pyfile,
                        "line": i,
                        "code": line.strip()
                    })
    return sql_patterns

# 2. Fetch current rules (stubbed)
def get_current_rules():
    # In a real implementation, fetch from API or read rule files
    return [
        {"rule_type": "testing_flow", "description": "Use Makefile.ai for all test runs."},
        {"rule_type": "precommit", "description": "All repos must use pre-commit hooks."}
    ]

# 3. Generate prompt for Ollama
def build_prompt(patterns, rules):
    prompt = """
You are an expert code reviewer and rule author.\n
Given these code patterns and the current rules, suggest new rules or improvements.\n
- Code patterns:\n"""
    for p in patterns:
        prompt += f"  - {p['file']}:{p['line']}: {p['code']}\n"
    prompt += "\n- Current rules:\n"
    for r in rules:
        prompt += f"  - {r['rule_type']}: {r['description']}\n"
    prompt += "\nRespond with a JSON array of rule proposals, each with: rule_type, description, diff, rationale, references, current_rule (if updating)."
    return prompt

# 4. Call Ollama LLM
def call_ollama(prompt):
    response = requests.post(OLLAMA_URL, json={"model": MODEL, "prompt": prompt})
    response.raise_for_status()
    # Ollama returns a streaming response; get the full text
    result = response.json()["response"]
    return result

# 5. Parse LLM output (expecting JSON array)
def parse_rule_proposals(llm_output):
    try:
        proposals = json.loads(llm_output)
        if not isinstance(proposals, list):
            raise ValueError("Expected a list of proposals")
        return proposals
    except Exception as e:
        print("Error parsing LLM output:", e)
        print("Raw output:", llm_output)
        return []

# 6. Submit proposals to API
def submit_proposals(proposals):
    for proposal in proposals:
        resp = requests.post(API_URL, json=proposal)
        if resp.ok:
            print(f"Submitted: {proposal.get('rule_type')} - {proposal.get('description')[:60]}...")
        else:
            print(f"Failed to submit: {proposal.get('rule_type')}", resp.text)

if __name__ == "__main__":
    print("Scanning codebase for patterns...")
    patterns = scan_codebase_for_patterns()
    print(f"Found {len(patterns)} patterns.")
    rules = get_current_rules()
    prompt = build_prompt(patterns, rules)
    print("Calling Ollama for rule proposals...")
    llm_output = call_ollama(prompt)
    print("LLM output received. Parsing...")
    proposals = parse_rule_proposals(llm_output)
    if proposals:
        print(f"Submitting {len(proposals)} proposals to API...")
        submit_proposals(proposals)
    else:
        print("No valid proposals generated.") 
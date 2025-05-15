from fastapi import FastAPI, Request, UploadFile, File
from pydantic import BaseModel
import os
import subprocess
import json
import requests
import sys
from typing import List, Optional
import re

app = FastAPI()

# Helper for Docker/host detection

def get_default_url(port, path):
    if os.environ.get("RUNNING_IN_DOCKER") == "1":
        host = "host.docker.internal"
    else:
        host = "localhost"
    return f"http://{host}:{port}{path}"

OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    get_default_url(11434, "/api/generate")
)
MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

class SuggestRequest(BaseModel):
    target: str = "."
    dry_run: Optional[bool] = False

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

def run_static_checker(target="."):
    result = subprocess.run([
        sys.executable, "scripts/suggest_rules.py", target
    ], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"suggest_rules.py failed: {result.stderr}")
    try:
        suggestions = json.loads(result.stdout)
    except Exception as e:
        raise RuntimeError(f"Failed to parse suggest_rules.py output as JSON: {e}")
    return suggestions

def build_llm_prompt(suggestions):
    prompt = (
        "You are an expert code reviewer and rule author. "
        "Given the following static code analysis findings, generate clear, actionable, and well-documented rule proposals. "
        "For each unique rule_type, provide: a rule name, a description, enforcement steps, and a code example. "
        "Respond ONLY with a valid JSON array of rule proposal objects. "
        "Do NOT include any text, markdown, or explanations before or after the JSON array. "
        "Your response MUST start with '[' and end with ']'. "
        "If you output anything other than a JSON array, it will be considered an error. "
        "If you cannot comply, output []. "
        "Here are the findings (in JSON):\n" + json.dumps(suggestions, indent=2)
    )
    return prompt

def call_ollama(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    print(f"[DEBUG] Sending to Ollama: {OLLAMA_URL} with payload: {json.dumps(payload)[:200]}...")
    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    print(f"[DEBUG] Ollama response status: {resp.status_code}")
    print(f"[DEBUG] Ollama response text: {resp.text[:500]}")
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "")

def parse_llm_output(llm_output):
    # Try to parse as JSON first
    try:
        return json.loads(llm_output)
    except Exception:
        pass
    # Fallback: parse markdown/text output for rule proposals
    # More robust: split on patterns like '**Rule', optional whitespace, optional number, optional colon, optional asterisks
    proposals = []
    rule_blocks = re.split(r'\n\s*\*\*?Rule\s*\d*:?\*?\*?\s*', llm_output)
    for block in rule_blocks[1:]:
        lines = block.strip().splitlines()
        # The first line may be the rule title or description
        title = lines[0].strip("* :") if lines else "Untitled Rule"
        desc = ""
        # Try to find a description line or use the first non-title line
        for line in lines[1:]:
            if line.lower().startswith("description:"):
                desc = line.split(":", 1)[-1].strip()
                break
            elif not desc and line.strip():
                desc = line.strip()
        proposals.append({"rule_type": title, "description": desc, "raw_block": block.strip()})
    return proposals

@app.post("/suggest-llm-rules")
def suggest_llm_rules(req: SuggestRequest):
    try:
        suggestions = run_static_checker(req.target)
        if not suggestions:
            return {"proposals": [], "message": "No suggestions found."}
        prompt = build_llm_prompt(suggestions)
        llm_output = call_ollama(prompt)
        try:
            proposals = parse_llm_output(llm_output)
            return {"proposals": proposals}
        except Exception as e:
            return {"error": f"Failed to parse LLM output: {e}", "raw_output": llm_output}
    except Exception as e:
        return {"error": str(e)}

@app.post("/review-code-file")
async def review_code_file(file: UploadFile = File(...)):
    """
    Accepts a single code file, sends its content to the LLM for review, and returns feedback as JSON.
    """
    content = (await file.read()).decode("utf-8", errors="ignore")
    prompt = (
        "You are an expert code reviewer. "
        "Given the following file, provide actionable feedback, suggestions, and highlight any issues or improvements. "
        "Respond ONLY with a valid JSON array of suggestions, each with: rule_type, description, and (optionally) diff. "
        "Do NOT include any text, markdown, or explanations before or after the JSON array. "
        "Your response MUST start with '[' and end with ']'. "
        "If you cannot comply, output []. "
        f"\nFilename: {file.filename}\n\nCode:\n{content}\n"
    )
    try:
        llm_output = call_ollama(prompt)
        try:
            feedback = json.loads(llm_output)
        except Exception:
            feedback = [llm_output.strip()]
    except Exception as e:
        feedback = [f"[ERROR] LLM call failed: {e}"]
    return feedback 
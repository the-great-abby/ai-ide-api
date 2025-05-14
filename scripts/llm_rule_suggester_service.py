from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
import subprocess
import json
import requests
import sys
from typing import List, Optional

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
        "Respond ONLY with a JSON array of rule proposal objects, no markdown, no explanations, no extra text. "
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
    try:
        start = llm_output.find("[")
        end = llm_output.rfind("]") + 1
        if start != -1 and end != -1:
            return json.loads(llm_output[start:end])
        return json.loads(llm_output)
    except Exception as e:
        return {"error": f"Failed to parse LLM output as JSON: {e}", "raw_output": llm_output}

@app.post("/suggest-llm-rules")
def suggest_llm_rules(req: SuggestRequest):
    try:
        suggestions = run_static_checker(req.target)
        if not suggestions:
            return {"proposals": [], "message": "No suggestions found."}
        prompt = build_llm_prompt(suggestions)
        llm_output = call_ollama(prompt)
        proposals = parse_llm_output(llm_output)
        return {"proposals": proposals}
    except Exception as e:
        return {"error": str(e)} 
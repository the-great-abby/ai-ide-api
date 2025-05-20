from fastapi import FastAPI, Request, UploadFile, File, Body
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

def call_ollama(chunk, prompt=None):
    if prompt is not None:
        full_prompt = f"{prompt}\n\n{chunk}"
    else:
        full_prompt = chunk
    payload = {
        "model": MODEL,
        "prompt": full_prompt,
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
        llm_output = call_ollama(suggestions, prompt)
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
        llm_output = call_ollama(content, prompt)
        try:
            feedback = json.loads(llm_output)
        except Exception:
            feedback = [llm_output.strip()]
    except Exception as e:
        feedback = [f"[ERROR] LLM call failed: {e}"]
    return feedback 

def chunk_text(text, max_tokens=2000):
    lines = text.splitlines()
    chunk = []
    chunks = []
    count = 0
    for line in lines:
        chunk.append(line)
        count += 1
        if count >= max_tokens:
            chunks.append("\n".join(chunk))
            chunk = []
            count = 0
    if chunk:
        chunks.append("\n".join(chunk))
    return chunks

VERBOSE_PROMPT = (
    "Provide a detailed, technical summary of the following git diff. "
    "List all changed files, describe the nature of the changes, highlight any new features, "
    "bug fixes, or breaking changes, and include code snippets for the most significant changes. "
    "Be as verbose and explicit as possible."
)
CONCISE_PROMPT = (
    "Summarize the following git diff. List changed files and main changes."
)

@app.post("/summarize-git-diff")
def summarize_git_diff(
    diff: str = Body(..., embed=True),
    concise: bool = Body(False, embed=True)
):
    prompt = CONCISE_PROMPT if concise else VERBOSE_PROMPT
    chunks = chunk_text(diff, max_tokens=2000)
    summaries = []
    for i, chunk in enumerate(chunks):
        summary = call_ollama(chunk, prompt)
        summaries.append(summary)
    return {
        "summaries": summaries,
        "combined": "\n\n".join(summaries),
        "chunks": len(chunks),
        "prompt": prompt
    } 
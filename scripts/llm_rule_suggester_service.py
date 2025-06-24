from fastapi import FastAPI, Request, UploadFile, File, Body
from pydantic import BaseModel
import os
import subprocess
import json
import requests
import sys
from typing import List, Optional, Dict, Any
import re
import time

app = FastAPI()

# Health check state tracking
_health_state = {
    "last_check": None,
    "response_times": [],
    "consecutive_failures": 0,
    "is_overloaded": False
}

# Health check configuration
HEALTH_CHECK_TIMEOUT = 30  # Increased from 5 seconds
MAX_RESPONSE_TIME = 10  # Consider overloaded if response > 10 seconds
MAX_CONSECUTIVE_FAILURES = 3
RESPONSE_TIME_WINDOW = 10  # Track last 10 response times

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
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q6_K")


class SuggestRequest(BaseModel):
    target: str = "."
    dry_run: Optional[bool] = False


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def update_health_state(response_time: float, success: bool):
    """Update health state with response time and success/failure."""
    global _health_state
    
    current_time = time.time()
    _health_state["last_check"] = current_time
    
    if success:
        _health_state["consecutive_failures"] = 0
        _health_state["response_times"].append(response_time)
        # Keep only last N response times
        if len(_health_state["response_times"]) > RESPONSE_TIME_WINDOW:
            _health_state["response_times"] = _health_state["response_times"][-RESPONSE_TIME_WINDOW:]
    else:
        _health_state["consecutive_failures"] += 1
    
    # Determine if overloaded based on response times
    if _health_state["response_times"]:
        avg_response_time = sum(_health_state["response_times"]) / len(_health_state["response_times"])
        _health_state["is_overloaded"] = avg_response_time > MAX_RESPONSE_TIME
    else:
        _health_state["is_overloaded"] = False


@app.get("/health")
def health_check():
    """Enhanced health check with load detection and response time monitoring."""
    global _health_state
    
    start_time = time.time()
    
    try:
        # Try a minimal POST to the Ollama backend
        payload = {"model": MODEL, "prompt": "ping", "stream": False}
        response = requests.post(OLLAMA_URL, json=payload, timeout=HEALTH_CHECK_TIMEOUT)
        
        response_time = time.time() - start_time
        success = response.status_code == 200 and "response" in response.json()
        
        update_health_state(response_time, success)
        
        if success:
            avg_response_time = sum(_health_state["response_times"]) / len(_health_state["response_times"]) if _health_state["response_times"] else 0
            
            return {
                "status": "ok" if not _health_state["is_overloaded"] else "degraded",
                "ollama_backend": "ok",
                "response_time": round(response_time, 2),
                "avg_response_time": round(avg_response_time, 2),
                "is_overloaded": _health_state["is_overloaded"],
                "consecutive_failures": _health_state["consecutive_failures"],
                "load_level": "high" if _health_state["is_overloaded"] else "normal"
            }
        else:
            update_health_state(response_time, False)
            return {
                "status": "error",
                "ollama_backend": f"bad status {response.status_code}",
                "response_time": round(response_time, 2),
                "consecutive_failures": _health_state["consecutive_failures"],
                "is_overloaded": _health_state["is_overloaded"]
            }
            
    except requests.exceptions.Timeout:
        response_time = time.time() - start_time
        update_health_state(response_time, False)
        return {
            "status": "error",
            "ollama_backend": f"timeout after {HEALTH_CHECK_TIMEOUT}s",
            "response_time": round(response_time, 2),
            "consecutive_failures": _health_state["consecutive_failures"],
            "is_overloaded": True
        }
    except Exception as e:
        response_time = time.time() - start_time
        update_health_state(response_time, False)
        return {
            "status": "error",
            "ollama_backend": f"unreachable: {e}",
            "response_time": round(response_time, 2),
            "consecutive_failures": _health_state["consecutive_failures"],
            "is_overloaded": _health_state["is_overloaded"]
        }


@app.get("/health/detailed")
def detailed_health_check():
    """Detailed health check with full load metrics."""
    global _health_state
    
    basic_health = health_check()
    
    # Add additional metrics
    detailed_health = {
        **basic_health,
        "metrics": {
            "response_time_history": _health_state["response_times"][-5:],  # Last 5 response times
            "total_checks": len(_health_state["response_times"]) + _health_state["consecutive_failures"],
            "success_rate": len(_health_state["response_times"]) / max(1, len(_health_state["response_times"]) + _health_state["consecutive_failures"]),
            "last_check_time": _health_state["last_check"],
            "time_since_last_check": time.time() - _health_state["last_check"] if _health_state["last_check"] else None
        },
        "recommendations": []
    }
    
    # Add recommendations based on health state
    if _health_state["is_overloaded"]:
        detailed_health["recommendations"].append("Consider reducing request frequency")
        detailed_health["recommendations"].append("Increase timeouts for requests")
    
    if _health_state["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
        detailed_health["recommendations"].append("Ollama may be down or severely overloaded")
    
    if _health_state["response_times"] and max(_health_state["response_times"]) > 30:
        detailed_health["recommendations"].append("Response times are very high - consider restarting Ollama")
    
    return detailed_health


def run_static_checker(target="."):
    result = subprocess.run(
        [sys.executable, "scripts/suggest_rules.py", target],
        capture_output=True,
        text=True,
    )
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


def call_ollama(chunk, prompt=None, timeout=None):
    """Call Ollama with circuit breaker pattern and adaptive timeout."""
    global _health_state
    
    # Circuit breaker: if overloaded, increase timeout or fail fast
    if _health_state["is_overloaded"]:
        if timeout is None:
            timeout = 180  # 3 minutes when overloaded
        elif timeout < 120:
            timeout = 120  # Minimum 2 minutes when overloaded
    
    # Use default timeout if not specified
    if timeout is None:
        timeout = 120  # 2 minutes default
    
    if prompt is not None:
        full_prompt = f"{prompt}\n\n{chunk}"
    else:
        full_prompt = chunk
    
    payload = {"model": MODEL, "prompt": full_prompt, "stream": False}
    
    print(f"[DEBUG] Sending to Ollama: {OLLAMA_URL} with timeout={timeout}s")
    print(f"[DEBUG] Payload preview: {json.dumps(payload)[:200]}...")
    
    start_time = time.time()
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response_time = time.time() - start_time
        
        print(f"[DEBUG] Ollama response status: {resp.status_code}")
        print(f"[DEBUG] Ollama response time: {response_time:.2f}s")
        print(f"[DEBUG] Ollama response preview: {resp.text[:500]}")
        
        resp.raise_for_status()
        data = resp.json()
        
        # Update health state with success
        update_health_state(response_time, True)
        
        return data.get("response", "")
        
    except requests.exceptions.Timeout:
        response_time = time.time() - start_time
        print(f"[ERROR] Ollama request timed out after {timeout}s")
        update_health_state(response_time, False)
        raise Exception(f"Ollama request timed out after {timeout}s")
        
    except Exception as e:
        response_time = time.time() - start_time
        print(f"[ERROR] Ollama request failed: {e}")
        update_health_state(response_time, False)
        raise


def parse_llm_output(llm_output):
    # Try to parse as JSON first
    try:
        return json.loads(llm_output)
    except Exception:
        pass
    # Fallback: parse markdown/text output for rule proposals
    # More robust: split on patterns like '**Rule', optional whitespace, optional number, optional colon, optional asterisks
    proposals = []
    rule_blocks = re.split(r"\n\s*\*\*?Rule\s*\d*:?\*?\*?\s*", llm_output)
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
        proposals.append(
            {"rule_type": title, "description": desc, "raw_block": block.strip()}
        )
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
            return {
                "error": f"Failed to parse LLM output: {e}",
                "raw_output": llm_output,
            }
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
    diff: str = Body(..., embed=True), concise: bool = Body(False, embed=True)
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
        "prompt": prompt,
    }


class EmbeddingRequest(BaseModel):
    text: str
    model: Optional[str] = "nomic-embed-text:latest"

class LLMRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    stream: Optional[bool] = False

@app.post("/generate")
def generate_text(request: LLMRequest):
    """
    Generate text using Ollama LLM.
    Proxies the request to Ollama's generate endpoint.
    """
    try:
        model = request.model or MODEL
        payload = {
            "model": model,
            "prompt": request.prompt,
            "stream": request.stream
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        if request.stream:
            # For streaming responses, return the raw response
            return response.text
        else:
            # For non-streaming responses, parse JSON
            result = response.json()
            return {
                "response": result.get("response", ""),
                "model": model,
                "prompt_length": len(request.prompt)
            }
    except Exception as e:
        return {"error": f"Text generation failed: {str(e)}"}, 500

@app.post("/embed-text")
def embed_text(request: EmbeddingRequest):
    """
    Generate embeddings for text using Ollama.
    Proxies the request to Ollama's embedding endpoint.
    """
    try:
        # Call Ollama's embedding endpoint
        ollama_embedding_url = get_default_url(11434, "/api/embeddings")
        payload = {"model": request.model, "prompt": request.text}

        response = requests.post(ollama_embedding_url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        return {
            "embedding": result.get("embedding", []),
            "model": request.model,
            "text_length": len(request.text),
        }
    except Exception as e:
        return {"error": f"Embedding generation failed: {str(e)}"}, 500


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LLM Rule Suggester Service CLI")
    parser.add_argument(
        "target", nargs="?", default=".", help="Target directory or file to analyze"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run static checker only (no LLM)"
    )
    args = parser.parse_args()
    try:
        suggestions = run_static_checker(args.target)
        print(json.dumps(suggestions, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

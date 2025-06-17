import os
import json
import logging
import subprocess
import requests
from typing import Dict, Any, Optional
import traceback

# --- LLM Prompt Example ---
# You are an opinionated software architect. Given the following git diff and commit metadata, do the following:
# 1. Summarize the changes in clear, technical language.
# 2. Categorize the changes (e.g., refactor, feature, bugfix, docs, etc.).
# 3. Suggest tags for the changes.
# 4. List any design decisions that are unclear or questionable as open questions.
# 5. Propose relationships between this summary and other possible memory nodes (e.g., related features, modules, or files).
# Please respond in the following JSON format:
# {
#   "summary": "string",
#   "categories": ["string", ...],
#   "tags": ["string", ...],
#   "open_questions": ["string", ...],
#   "related_files": ["string", ...],
#   "proposed_relationships": [
#     {"type": "relates_to", "target": "string (e.g., file, feature, or node id if known)"}
#   ]
# }

def get_api_token():
    token = os.environ.get("MEMORY_API_TOKEN")
    if not token:
        try:
            with open("/code/.apitoken") as f:
                token = f.read().strip()
        except Exception:
            token = "changeme"  # fallback or raise error
    return token

MEMORY_API_URL = os.environ.get("MEMORY_API_URL", "http://test-api:8000/memory")
OLLAMA_FUNCTIONS_URL = os.environ.get("OLLAMA_FUNCTIONS_URL", "http://ollama-functions:8000")
MEMORY_API_TOKEN = get_api_token()
DEFAULT_NAMESPACE = os.environ.get("MEMORY_NAMESPACE", "progress_reports")

logger = logging.getLogger("progress_report_worker")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

HEAD_COMMIT_NODE_META_KEY = "last_processed_commit"

ENABLE_DIFF_SUMMARIZATION = os.environ.get("ENABLE_DIFF_SUMMARIZATION", "true").lower() in ("1", "true", "yes")

def get_last_processed_commit() -> Optional[str]:
    """Fetch the last processed commit hash from memory nodes."""
    headers = {"Authorization": f"Bearer {MEMORY_API_TOKEN}"}
    resp = requests.get(f"{MEMORY_API_URL}/nodes?namespace={DEFAULT_NAMESPACE}", headers=headers)
    logger.debug(f"GET /nodes response: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    nodes = resp.json()
    for node in nodes:
        meta = node.get("meta")
        if meta and isinstance(meta, dict) and meta.get("type") == HEAD_COMMIT_NODE_META_KEY:
            return node.get("content")
    return None

def update_last_processed_commit(commit_hash: str) -> None:
    """Create or update the last processed commit node."""
    headers = {"Authorization": f"Bearer {MEMORY_API_TOKEN}"}
    payload = {
        "namespace": DEFAULT_NAMESPACE,
        "content": commit_hash,
        "meta": json.dumps({"type": HEAD_COMMIT_NODE_META_KEY})
    }
    resp = requests.post(f"{MEMORY_API_URL}/nodes", json=payload, headers=headers)
    logger.debug(f"POST /nodes (last commit) response: {resp.status_code} {resp.text}")
    resp.raise_for_status()

def get_git_diff(base_commit: str, head_commit: str = "HEAD") -> str:
    """Get the git diff between two commits."""
    result = subprocess.run(["git", "diff", base_commit, head_commit], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"git diff failed: {result.stderr}")
        raise RuntimeError("git diff failed")
    return result.stdout

def call_llm_summarize(diff: str, commit_msg: str, author: str) -> Dict[str, Any]:
    """Call the Ollama LLM summarization endpoint."""
    prompt = {
        "diff": diff,
        "commit_msg": commit_msg,
        "author": author,
        "instructions": "You are an opinionated software architect. Summarize, categorize, tag, and list open questions for this diff. Respond in the required JSON format."
    }
    resp = requests.post(f"{OLLAMA_FUNCTIONS_URL}/summarize-git-diff", json=prompt, timeout=120)
    logger.debug(f"POST /summarize-git-diff response: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    return resp.json()

def create_memory_node(content: str, meta: Dict[str, Any]) -> str:
    headers = {"Authorization": f"Bearer {MEMORY_API_TOKEN}"}
    payload = {
        "namespace": DEFAULT_NAMESPACE,
        "content": content,
        "meta": json.dumps(meta) if isinstance(meta, dict) else meta
    }
    logger.debug(f"[create_memory_node] Sending payload: {json.dumps(payload)}")
    try:
        resp = requests.post(f"{MEMORY_API_URL}/nodes", json=payload, headers=headers)
        logger.debug(f"[create_memory_node] Response status: {resp.status_code}, text: {resp.text}")
        resp.raise_for_status()
        return resp.json()["id"]
    except Exception as exc:
        logger.error(f"[create_memory_node] Exception: {exc}")
        raise

def create_memory_edge(from_id: str, to_id: str, relation_type: str, meta: Optional[Dict[str, Any]] = None) -> None:
    headers = {"Authorization": f"Bearer {MEMORY_API_TOKEN}"}
    payload = {
        "from_id": from_id,
        "to_id": to_id,
        "relation_type": relation_type,
        "meta": meta or {}
    }
    resp = requests.post(f"{MEMORY_API_URL}/edges", json=payload, headers=headers)
    logger.debug(f"POST /edges response: {resp.status_code} {resp.text}")
    resp.raise_for_status()

async def process_progress_report_job(body: Dict[str, Any]):
    logger.debug(f"[process_progress_report_job] Received job body: {body}")
    try:
        # 1. Get last processed commit
        logger.debug("[process_progress_report_job] Fetching last processed commit...")
        last_commit = get_last_processed_commit()
        logger.debug(f"[process_progress_report_job] Last processed commit: {last_commit}")
        head_commit = "HEAD"
        if not last_commit:
            # Fallback: use previous commit
            last_commit = "HEAD~1"
        # 2. Get git diff
        logger.debug(f"[process_progress_report_job] Getting git diff from {last_commit} to {head_commit}...")
        diff = get_git_diff(last_commit, head_commit)
        logger.debug(f"[process_progress_report_job] Git diff: {diff[:200]}..." if diff else "[process_progress_report_job] No diff found.")
        if not diff.strip():
            logger.info("No changes detected since last processed commit.")
            return
        # 3. Get commit metadata
        logger.debug("[process_progress_report_job] Getting commit metadata...")
        commit_msg = subprocess.run(["git", "log", "-1", "--pretty=%s"], capture_output=True, text=True).stdout.strip()
        author = subprocess.run(["git", "log", "-1", "--pretty=%an"], capture_output=True, text=True).stdout.strip()
        logger.debug(f"[process_progress_report_job] Commit msg: {commit_msg}, Author: {author}")

        if ENABLE_DIFF_SUMMARIZATION:
            logger.debug("[process_progress_report_job] Diff summarization enabled. Calling LLM...")
            # 4. Call LLM
            try:
                llm_result = call_llm_summarize(diff, commit_msg, author)
                logger.debug(f"[process_progress_report_job] LLM result: {llm_result}")
            except Exception as e:
                logger.error(f"[process_progress_report_job] Exception during LLM call: {e}")
                logger.error(traceback.format_exc())
                raise
            # 5. Create summary node
            try:
                summary_text = llm_result.get("summary")
                if not summary_text:
                    summary_text = llm_result.get("combined")
                if not summary_text and "summaries" in llm_result and isinstance(llm_result["summaries"], list) and llm_result["summaries"]:
                    summary_text = llm_result["summaries"][0]
                if not summary_text:
                    logger.error(f"[process_progress_report_job] No summary found in LLM result: {llm_result}")
                    raise KeyError("No summary found in LLM result")
                summary_id = create_memory_node(summary_text, {
                    "categories": llm_result.get("categories", []),
                    "tags": llm_result.get("tags", []),
                    "related_files": llm_result.get("related_files", []),
                    "type": "progress_report"
                })
                logger.debug(f"[process_progress_report_job] Created summary node with id: {summary_id}")
            except Exception as e:
                logger.error(f"[process_progress_report_job] Exception during summary node creation: {e}")
                logger.error(traceback.format_exc())
                raise
            # 6. Create open question nodes and edges
            for question in llm_result.get("open_questions", []):
                try:
                    q_id = create_memory_node(question, {"type": "open_question"})
                    create_memory_edge(summary_id, q_id, "has_open_question")
                    logger.debug(f"[process_progress_report_job] Created open question node {q_id} and edge from {summary_id}")
                except Exception as e:
                    logger.error(f"[process_progress_report_job] Exception during open question node/edge: {e}")
                    logger.error(traceback.format_exc())
            # 7. Create relationships to related files
            for file in llm_result.get("related_files", []):
                try:
                    f_id = create_memory_node(file, {"type": "related_file"})
                    create_memory_edge(summary_id, f_id, "relates_to")
                    logger.debug(f"[process_progress_report_job] Created related file node {f_id} and edge from {summary_id}")
                except Exception as e:
                    logger.error(f"[process_progress_report_job] Exception during related file node/edge: {e}")
                    logger.error(traceback.format_exc())
        else:
            logger.info("Diff summarization is DISABLED. Creating placeholder summary node.")
            placeholder = f"[Summarization disabled] Diff from {last_commit} to {head_commit}. Commit message: {commit_msg}"
            try:
                summary_id = create_memory_node(placeholder, {
                    "type": "progress_report",
                    "tags": ["summarization_disabled"],
                    "categories": [],
                    "related_files": []
                })
                logger.info(f"Created placeholder summary node with id: {summary_id}")
            except Exception as e:
                logger.error(f"[process_progress_report_job] Exception during placeholder node creation: {e}")
                logger.error(traceback.format_exc())
                raise

        # 8. Create proposed relationships
        for rel in llm_result.get("proposed_relationships", []):
            target = rel.get("target")
            if target:
                try:
                    t_id = create_memory_node(target, {"type": rel.get("type", "related")})
                    create_memory_edge(summary_id, t_id, rel.get("type", "related"))
                    logger.debug(f"[process_progress_report_job] Created proposed relationship node {t_id} and edge from {summary_id}")
                except Exception as e:
                    logger.error(f"[process_progress_report_job] Exception during proposed relationship node/edge: {e}")
                    logger.error(traceback.format_exc())
        # 9. Update last processed commit
        try:
            new_commit = subprocess.run(["git", "rev-parse", head_commit], capture_output=True, text=True).stdout.strip()
            update_last_processed_commit(new_commit)
            logger.info(f"Progress report processed for commit {new_commit}")
        except Exception as e:
            logger.error(f"[process_progress_report_job] Exception during last commit update: {e}")
            logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"[process_progress_report_job] Unhandled exception: {e}")
        logger.error(traceback.format_exc()) 
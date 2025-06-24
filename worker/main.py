#!/usr/bin/env python3
# External Project Worker Main
# Generated on 2025-06-23 09:24:11
# Project: ai-ide-api_internal
# Note: External workers use API endpoints instead of direct Ollama Functions access

print('=== EXTERNAL WORKER MAIN.PY EXECUTING ===')
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('worker').info('=== EXTERNAL WORKER MAIN.PY EXECUTING ===')

import json
import os
import time
import asyncio
from utils.message_broker import RealRabbitMQClient, MessageBrokerBase
import requests

# Import worker modules (these should be copied from the main project)
process_progress_report_job = None
process_memory_cleanup_job = None
process_enrichment_job = None
process_similarity_pruning_job = None
process_git_history_analysis_job = None
missing_handlers = []
try:
    from worker.progress_report_worker import process_progress_report_job
except ImportError as e:
    print(f"Warning: Could not import process_progress_report_job: {e}")
    missing_handlers.append("process_progress_report_job")
try:
    from scripts.memory_cleanup_worker import process_memory_cleanup_job
except ImportError as e:
    print(f"Warning: Could not import process_memory_cleanup_job: {e}")
    missing_handlers.append("process_memory_cleanup_job")
try:
    from scripts.memory_enrichment_worker import process_enrichment_job
except ImportError as e:
    print(f"Warning: Could not import process_enrichment_job: {e}")
    missing_handlers.append("process_enrichment_job")
try:
    from scripts.memory_similarity_pruning_worker import process_similarity_pruning_job
except ImportError as e:
    print(f"Warning: Could not import process_similarity_pruning_job: {e}")
    missing_handlers.append("process_similarity_pruning_job")
try:
    from scripts.git_history_worker import process_git_history_analysis_job
except ImportError as e:
    print(f"Warning: Could not import process_git_history_analysis_job: {e}")
    missing_handlers.append("process_git_history_analysis_job")
if missing_handlers:
    print(f"Some worker functionality may not be available: {', '.join(missing_handlers)}")

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:9103")
MEMORY_API_TOKEN = os.environ.get("MEMORY_API_TOKEN", "")

PROGRESS_QUEUE = "progress.report"
MEMORY_CLEANUP_QUEUE = "memory.cleanup"
MEMORY_ENRICHMENT_QUEUE = "memory.enrichment"
MEMORY_SIMILARITY_QUEUE = "memory.similarity"
GIT_HISTORY_QUEUE = "git.history.analysis"
MEMORY_UPDATE_QUEUE = "memory.update"

logger = logging.getLogger("external_worker")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# External workers can now process git diff summarization via API
async def process_git_diff_job(body):
    """Process git diff summarization using the API endpoint."""
    if "diff" not in body:
        logger.info("No 'diff' field found in job")
        return {"status": "error", "reason": "missing_diff_field"}
    
    concise = body.get("concise", True)
    payload = {"diff": body["diff"], "concise": concise}
    
    try:
        # Use the API endpoint instead of direct Ollama Functions access
        headers = {"Authorization": f"Bearer {MEMORY_API_TOKEN}", "Content-Type": "application/json"}
        response = requests.post(
            f"{API_BASE_URL}/summarize-git-diff", 
            json=payload, 
            headers=headers,
            timeout=180
        )
        response.raise_for_status()
        summary = response.json()
        logger.info("Git diff summary response: %s", json.dumps(summary, indent=2))
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error("Error calling git diff summarization API: %s", e)
        return {"status": "error", "reason": str(e)}

# Available job handlers for external workers (now including git diff summarization)
JOB_HANDLERS = {}
if process_git_diff_job is not None:
    JOB_HANDLERS[MEMORY_UPDATE_QUEUE] = process_git_diff_job
if process_progress_report_job is not None:
    JOB_HANDLERS[PROGRESS_QUEUE] = process_progress_report_job
if process_memory_cleanup_job is not None:
    JOB_HANDLERS[MEMORY_CLEANUP_QUEUE] = process_memory_cleanup_job
if process_enrichment_job is not None:
    JOB_HANDLERS[MEMORY_ENRICHMENT_QUEUE] = process_enrichment_job
if process_similarity_pruning_job is not None:
    JOB_HANDLERS[MEMORY_SIMILARITY_QUEUE] = process_similarity_pruning_job
if process_git_history_analysis_job is not None:
    JOB_HANDLERS[GIT_HISTORY_QUEUE] = process_git_history_analysis_job

async def main(broker: MessageBrokerBase = None):
    logger.info("=== EXTERNAL WORKER STARTING ===")
    logger.info(f"Available job handlers: {list(JOB_HANDLERS.keys())}")
    logger.info("✅ Git diff summarization available via API endpoint")
    logger.info(f"API Base URL: {API_BASE_URL}")

    if broker is None:
        logger.info("Creating new RabbitMQ client...")
        broker = RealRabbitMQClient(RABBITMQ_URL)

    logger.info(f"Broker instance type: {type(broker).__name__}")
    logger.info("External worker started, polling for jobs...")
    print("External worker started, polling for jobs...")

    while True:
        for queue_name, handler in JOB_HANDLERS.items():
            logger.debug(f"About to poll queue: {queue_name}")
            try:
                # Consume from queue
                body = await broker.consume(queue_name)
                logger.debug(f"Polled queue {queue_name}, got body: {body}")
                
                if body is None:
                    logger.debug(f"No message in queue {queue_name}, sleeping...")
                    await asyncio.sleep(1)
                    continue
                
                # Parse job data
                try:
                    if isinstance(body, str):
                        job_data = json.loads(body)
                    else:
                        job_data = body
                    logger.info(f"🎯 Processing job from queue {queue_name}: {job_data}")
                    print(f"=== JOB DEQUEUED FROM {queue_name} ===")
                    
                    # Call handler
                    logger.info(f"🚀 Calling handler for {queue_name}")
                    result = await handler(job_data)
                    logger.info(f"✅ Handler for {queue_name} completed: {result}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse job data from {queue_name}: {e}")
                    logger.error(f"Raw body: {body}")
                except Exception as e:
                    logger.error(f"❌ Handler error for {queue_name}: {e}")
                    
            except Exception as e:
                logger.error(f"❌ Error polling queue {queue_name}: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

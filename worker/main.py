print('=== WORKER MAIN.PY EXECUTING (print) ===')
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('worker').info('=== WORKER MAIN.PY EXECUTING (logger) ===')
# Worker job dispatch pattern:
# To add a new job type:
# 1. Implement an async handler (e.g., process_new_job) in a module.
# 2. Add the queue name and handler to JOB_HANDLERS.
# 3. Ensure the queue is published to by the relevant producer.

import json
import os
import time
import asyncio
from utils.message_broker import RealRabbitMQClient, MessageBrokerBase
import requests
from worker.progress_report_worker import process_progress_report_job
from scripts.memory_cleanup_worker import process_memory_cleanup_job
from scripts.memory_enrichment_worker import process_enrichment_job
from scripts.memory_similarity_pruning_worker import process_similarity_pruning_job
from scripts.git_history_worker import process_git_history_analysis_job

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
QUEUE_NAME = "memory.update"
PROGRESS_QUEUE = "progress.report"
MEMORY_CLEANUP_QUEUE = "memory.cleanup"
MEMORY_ENRICHMENT_QUEUE = "memory.enrichment"
MEMORY_SIMILARITY_QUEUE = "memory.similarity"
GIT_HISTORY_QUEUE = "git.history.analysis"
OLLAMA_FUNCTIONS_URL = os.environ.get(
    "OLLAMA_FUNCTIONS_URL", "http://ollama-functions:8000"
)

logger = logging.getLogger("worker")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


async def process_job(body):
    if "diff" not in body:
        logger.info("No 'diff' field found in job")
        return
    concise = body.get("concise", True)
    payload = {"diff": body["diff"], "concise": concise}
    try:
        response = requests.post(
            f"{OLLAMA_FUNCTIONS_URL}/summarize-git-diff", json=payload, timeout=60
        )
        response.raise_for_status()
        summary = response.json()
        logger.info("Summary response: %s", json.dumps(summary, indent=2))
    except Exception as e:
        logger.error("Error calling Ollama Functions API: %s", e)


JOB_HANDLERS = {
    QUEUE_NAME: process_job,
    PROGRESS_QUEUE: process_progress_report_job,
    MEMORY_CLEANUP_QUEUE: process_memory_cleanup_job,
    MEMORY_ENRICHMENT_QUEUE: process_enrichment_job,
    MEMORY_SIMILARITY_QUEUE: process_similarity_pruning_job,
    GIT_HISTORY_QUEUE: process_git_history_analysis_job,
}


async def main(broker: MessageBrokerBase = None):
    logger.info("=== WORKER STARTING ===")
    logger.info(f"Job handlers configured: {list(JOB_HANDLERS.keys())}")

    if broker is None:
        logger.info("Creating new RabbitMQ client...")
        broker = RealRabbitMQClient(RABBITMQ_URL)

    logger.info(f"Broker instance type: {type(broker).__name__}")
    logger.info(f"Broker instance: {broker}")
    logger.info("Worker started, polling for jobs...")
    print("Worker started, polling for jobs...")

    while True:
        for queue_name, handler in JOB_HANDLERS.items():
            logger.debug(f"About to poll queue: {queue_name}")
            try:
                # Consume from queue
                body = await broker.consume(queue_name)
                logger.debug(f"Polled queue {queue_name}, got body: {body}")
                logger.debug(f"Body type: {type(body)}")
                
                if body is None:
                    logger.debug(f"No message in queue {queue_name}, sleeping...")
                    await asyncio.sleep(1)
                    continue
                
                # Parse job data
                try:
                    # The message broker already returns parsed JSON, so body is already a dict
                    if isinstance(body, str):
                        job_data = json.loads(body)
                    else:
                        job_data = body
                    logger.info(f"🎯 Processing job from queue {queue_name}: {job_data}")
                    print(f"=== JOB DEQUEUED FROM {queue_name} ===")
                    logger.critical(f"=== JOB DEQUEUED FROM {queue_name} (CRITICAL) ===")
                    
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

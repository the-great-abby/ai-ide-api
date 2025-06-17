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
import logging
from progress_report_worker import process_progress_report_job

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
QUEUE_NAME = "memory.update"
PROGRESS_QUEUE = "progress.report"
OLLAMA_FUNCTIONS_URL = os.environ.get(
    "OLLAMA_FUNCTIONS_URL", "http://ollama-functions:8000"
)

logger = logging.getLogger("worker")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
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
}

async def main(broker: MessageBrokerBase = None):
    if broker is None:
        broker = RealRabbitMQClient(RABBITMQ_URL)
    print("Worker started, polling for jobs...")
    while True:
        for queue, handler in JOB_HANDLERS.items():
            body = await broker.consume(queue)
            logger.debug(f"Polled queue {queue}, got body: {body}")
            if body:
                try:
                    await handler(body)
                except Exception as e:
                    print(f"Error processing job from {queue}:", e)
            else:
                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

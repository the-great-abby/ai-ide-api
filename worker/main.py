import json
import os
import time
import asyncio
from utils.message_broker import RealRabbitMQClient, MessageBrokerBase
import requests

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
QUEUE_NAME = "memory.update"
OLLAMA_FUNCTIONS_URL = os.environ.get(
    "OLLAMA_FUNCTIONS_URL", "http://ollama-functions:8000"
)

async def process_job(body):
    print("Processing job:", body)
    diff = body.get("diff")
    if not diff:
        print("No 'diff' field found in job. Skipping.")
        return
    concise = body.get("concise", True)
    payload = {"diff": diff, "concise": concise}
    try:
        response = requests.post(
            f"{OLLAMA_FUNCTIONS_URL}/summarize-git-diff", json=payload, timeout=60
        )
        response.raise_for_status()
        summary = response.json()
        print("Summary response:", json.dumps(summary, indent=2))
    except Exception as e:
        print("Error calling Ollama Functions API:", e)

async def main(broker: MessageBrokerBase = None):
    if broker is None:
        broker = RealRabbitMQClient(RABBITMQ_URL)
    print("Worker started, polling for jobs...")
    while True:
        body = await broker.consume(QUEUE_NAME)
        if body:
            try:
                await process_job(body)
            except Exception as e:
                print("Error processing job:", e)
        else:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

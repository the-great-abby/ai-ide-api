import json
import os
import time

import pika
import requests

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
QUEUE_NAME = "memory.update"
OLLAMA_FUNCTIONS_URL = os.environ.get(
    "OLLAMA_FUNCTIONS_URL", "http://ollama-functions:8000"
)


def process_job(body):
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


def main():
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    print("Worker started, polling for jobs...")
    while True:
        method_frame, header_frame, body = channel.basic_get(QUEUE_NAME)
        if method_frame:
            try:
                process_job(json.loads(body))
                channel.basic_ack(method_frame.delivery_tag)
            except Exception as e:
                print("Error processing job:", e)
        else:
            time.sleep(1)


if __name__ == "__main__":
    main()

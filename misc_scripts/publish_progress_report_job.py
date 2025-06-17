import pika
import json
import os

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@localhost:5672/")
QUEUE = "progress.report"

print(f"Connecting to: {RABBITMQ_URL}")
connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
channel = connection.channel()
channel.queue_declare(queue=QUEUE, durable=True)

# Send a non-empty test message for clarity
test_body = {"test": "hello", "source": "manual-script"}
print(f"Publishing to queue: {QUEUE}")
print(f"Message body: {json.dumps(test_body)}")
channel.basic_publish(exchange="", routing_key=QUEUE, body=json.dumps(test_body))
print("Published progress report job.")
connection.close() 
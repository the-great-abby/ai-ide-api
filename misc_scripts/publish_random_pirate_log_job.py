import pika
import json
import os
from datetime import datetime

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@localhost:5672/")
QUEUE = "pirate.log.random"

print(f"Connecting to: {RABBITMQ_URL}")
connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
channel = connection.channel()
channel.queue_declare(queue=QUEUE, durable=True)

body = {
    "trigger": "random_pirate_log_entry",
    "timestamp": datetime.now().isoformat(),
    "source": "publish_random_pirate_log_job.py"
}
print(f"Publishing to queue: {QUEUE}")
print(f"Message body: {json.dumps(body)}")
channel.basic_publish(exchange="", routing_key=QUEUE, body=json.dumps(body))
print("Published random pirate log job.")
connection.close() 
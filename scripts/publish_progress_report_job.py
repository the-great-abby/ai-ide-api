import pika
import json
import os

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@localhost:5672/")
QUEUE = "progress.report"

connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
channel = connection.channel()
channel.queue_declare(queue=QUEUE, durable=True)

# The body can be empty or include extra info if you want to extend the worker
body = {}
channel.basic_publish(exchange="", routing_key=QUEUE, body=json.dumps(body))
print("Published progress report job.")
connection.close() 
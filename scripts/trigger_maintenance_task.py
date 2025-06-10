#!/usr/bin/env python3
import sys, json, pika, os

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = os.environ.get("MAINTENANCE_QUEUE", "maintenance")

def publish_task(task, args=None):
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    body = json.dumps({"task": task, "args": args or {}})
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=body)
    print(f"[PUBLISHED] task={task} args={args}")
    connection.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: trigger_maintenance_task.py <task> [key=value ...]")
        sys.exit(1)
    task = sys.argv[1]
    args = dict(arg.split("=", 1) for arg in sys.argv[2:])
    publish_task(task, args) 
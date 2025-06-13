#!/usr/bin/env python3
import sys, json, os, asyncio
from utils.message_broker import RealRabbitMQClient, MessageBrokerBase

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = os.environ.get("MAINTENANCE_QUEUE", "maintenance")

async def publish_task(task, args=None, broker: MessageBrokerBase = None):
    if broker is None:
        broker = RealRabbitMQClient(f"amqp://user:password@{RABBITMQ_HOST}:5672/")
    body = {"task": task, "args": args or {}}
    await broker.publish(QUEUE_NAME, body)
    print(f"[PUBLISHED] task={task} args={args}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: trigger_maintenance_task.py <task> [key=value ...]")
        sys.exit(1)
    task = sys.argv[1]
    args = dict(arg.split("=", 1) for arg in sys.argv[2:])
    asyncio.run(publish_task(task, args)) 
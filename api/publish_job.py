import json
import os
from utils.message_broker import RealRabbitMQClient, MessageBrokerBase

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
QUEUE_NAME = "memory.update"

async def publish_job(job_data, broker: MessageBrokerBase = None):
    if broker is None:
        broker = RealRabbitMQClient(RABBITMQ_URL)
    await broker.publish(QUEUE_NAME, job_data)

#!/usr/bin/env python3
import asyncio
import sys

sys.path.append("/app/utils")
from message_broker import RealRabbitMQClient


async def test_consume_only():
    broker = RealRabbitMQClient("amqp://user:password@rabbitmq:5672/")
    print("Attempting to consume from git.history.analysis queue...")

    # Try to consume a message
    body = await broker.consume("git.history.analysis")
    print(f"Consumed message: {body}")

    if body:
        print("Message found!")
        print(f"Message type: {type(body)}")
        print(
            f"Message keys: {list(body.keys()) if isinstance(body, dict) else 'Not a dict'}"
        )
        return True
    else:
        print("No message found")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_consume_only())
    print(f"Test result: {result}")

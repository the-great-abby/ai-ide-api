from typing import Any, Optional
from utils.message_broker import MessageBrokerBase
import asyncio


class MockRabbitMQ(MessageBrokerBase):
    """
    Mock RabbitMQ client for unit tests. Uses in-memory queues.
    """

    def __init__(self):
        self.queues = {}
        self.lock = asyncio.Lock()

    async def publish(self, queue: str, message: Any):
        async with self.lock:
            self.queues.setdefault(queue, []).append(message)

    async def consume(self, queue: str) -> Optional[Any]:
        async with self.lock:
            if self.queues.get(queue):
                return self.queues[queue].pop(0)
            return None

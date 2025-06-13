from typing import Any, Optional
import asyncio

class MessageBrokerBase:
    """
    Abstract base class for message brokers. All message brokers (real or mock) should implement this interface.
    """
    async def publish(self, queue: str, message: Any):
        raise NotImplementedError

    async def consume(self, queue: str) -> Optional[Any]:
        raise NotImplementedError


class RealRabbitMQClient(MessageBrokerBase):
    """
    Real RabbitMQ client using pika (blocking, wrapped for async compatibility).
    Matches the MessageBrokerBase interface.
    """
    def __init__(self, url: str):
        import pika
        self._url = url
        self._params = pika.URLParameters(url)

    async def publish(self, queue: str, message: Any):
        import pika
        import json
        def _publish():
            connection = pika.BlockingConnection(self._params)
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            connection.close()
        await asyncio.to_thread(_publish)

    async def consume(self, queue: str) -> Optional[Any]:
        import pika
        import json
        def _consume():
            connection = pika.BlockingConnection(self._params)
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=True)
            method_frame, header_frame, body = channel.basic_get(queue)
            if method_frame:
                channel.basic_ack(method_frame.delivery_tag)
                result = json.loads(body)
            else:
                result = None
            connection.close()
            return result
        return await asyncio.to_thread(_consume) 
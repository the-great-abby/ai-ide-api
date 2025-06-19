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

        print(f"[DEBUG] PUBLISH CALLED for queue: {queue}")
        print(f"[DEBUG] Message to publish: {message}")

        def _publish():
            print(f"[DEBUG] Inside _publish function for queue: {queue}")
            connection = pika.BlockingConnection(self._params)
            print(f"[DEBUG] Connection established")
            channel = connection.channel()
            print(f"[DEBUG] Channel created")
            channel.queue_declare(queue=queue, durable=True)
            print(f"[DEBUG] Queue declared: {queue}")
            body = json.dumps(message)
            print(f"[DEBUG] Message body: {body}")
            channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=body,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            print(f"[DEBUG] Message published successfully")
            connection.close()
            print(f"[DEBUG] Connection closed")

        await asyncio.to_thread(_publish)
        print(f"[DEBUG] Publish completed for queue: {queue}")

    async def consume(self, queue: str) -> Optional[Any]:
        print(f"[DEBUG] CONSUME CALLED for queue: {queue}")
        import pika
        import json

        def _consume():
            connection = pika.BlockingConnection(self._params)
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=True)
            method_frame, header_frame, body = channel.basic_get(queue)
            print(f"[DEBUG] Raw message from queue '{queue}': {body}")
            if method_frame:
                channel.basic_ack(method_frame.delivery_tag)
                try:
                    result = json.loads(body)
                    print(f"[DEBUG] Decoded message: {result}")
                except Exception as e:
                    print(f"[ERROR] Failed to decode message: {e}")
                    result = None
            else:
                result = None
            connection.close()
            return result

        return await asyncio.to_thread(_consume)

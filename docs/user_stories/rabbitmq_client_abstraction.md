# User Story: RabbitMQ Client Abstraction for Swappable Real and Mock Services

## Motivation
To enable fast, reliable unit testing and easy service mocking, all RabbitMQ (message broker) usage in the codebase should go through a client abstraction. This allows seamless swapping between a real RabbitMQ client (for production/integration) and a mock client (for unit tests), improving test speed and reliability.

## Actors
- Developers writing features that use RabbitMQ
- Test authors needing to mock message brokers
- CI/CD systems running tests

## Preconditions
- The codebase includes a `MessageBrokerBase` interface and both real and mock implementations.

## Step-by-Step Actions
1. **Use the Abstraction**
   - Import and use `MessageBrokerBase` (or a subclass) for all message broker operations.
   - Do not use the RabbitMQ library directly in application code.

2. **Inject the Client**
   - Pass the message broker client as a dependency (e.g., via function arguments or fixtures).
   - In production, use `RealRabbitMQClient`.
   - In unit tests, use `MockRabbitMQ`.

3. **Example Usage**
```python
# In application code
from utils.message_broker import MessageBrokerBase

async def queue_task(broker: MessageBrokerBase, queue: str, task: dict):
    await broker.publish(queue, task)

# In production setup
from utils.message_broker import RealRabbitMQClient
broker = RealRabbitMQClient(url="amqp://user:password@rabbitmq:5672/")

# In unit tests
from mocks.mock_rabbitmq import MockRabbitMQ
broker = MockRabbitMQ()
```

## Expected Outcomes
- All message broker usage is swappable between real and mock clients.
- Unit tests run quickly and do not require a running RabbitMQ service.
- Integration tests and production use the real RabbitMQ service.

## Best Practices
- Always use the client abstraction, never the RabbitMQ library directly.
- Keep the mock interface in sync with the real client.
- Use dependency injection to swap clients easily.
- Document any limitations of the mock client.

## References
- See `utils/message_broker.py` for the abstraction and real client.
- See `mocks/mock_rabbitmq.py` for the mock implementation. 
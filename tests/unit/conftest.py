import pytest
from mocks.mock_rabbitmq import MockRabbitMQ


@pytest.fixture
def mock_rabbitmq():
    """
    Provides a fresh MockRabbitMQ instance for each test.
    Usage:
        def test_something(mock_rabbitmq):
            await mock_rabbitmq.publish('queue', {'foo': 'bar'})
            msg = await mock_rabbitmq.consume('queue')
            assert msg == {'foo': 'bar'}
    """
    return MockRabbitMQ()

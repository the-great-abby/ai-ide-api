# User Story: Redis Client Abstraction for Swappable Real and Mock Services

## Motivation
To enable fast, reliable unit testing and easy service mocking, all Redis usage in the codebase should go through a client abstraction. This allows seamless swapping between a real Redis client (for production/integration) and a mock client (for unit tests), improving test speed and reliability.

## Actors
- Developers writing features that use Redis
- Test authors needing to mock Redis
- CI/CD systems running tests

## Preconditions
- The codebase includes a `RedisClientBase` interface and both real and mock implementations.

## Step-by-Step Actions
1. **Use the Abstraction**
   - Import and use `RedisClientBase` (or a subclass) for all Redis operations.
   - Do not use the Redis library directly in application code.

2. **Inject the Client**
   - Pass the Redis client as a dependency (e.g., via function arguments, FastAPI Depends, or pytest fixtures).
   - In production, use `RealRedisClient`.
   - In unit tests, use `MockRedis`.

3. **Example Usage**
```python
# In application code
from utils.redis_client import RedisClientBase

async def cache_user(redis: RedisClientBase, user_id: str, data: dict):
    await redis.set(f"user:{user_id}", data)

# In production setup
from utils.redis_client import RealRedisClient
redis = RealRedisClient(host="db-redis", port=6379)

# In unit tests
from mocks.mock_redis import MockRedis
redis = MockRedis()
```

## Expected Outcomes
- All Redis usage is swappable between real and mock clients.
- Unit tests run quickly and do not require a running Redis service.
- Integration tests and production use the real Redis service.

## Best Practices
- Always use the client abstraction, never the Redis library directly.
- Keep the mock interface in sync with the real client.
- Use dependency injection to swap clients easily.
- Document any limitations of the mock client.

## References
- See `utils/redis_client.py` for the abstraction and real client.
- See `mocks/mock_redis.py` for the mock implementation. 
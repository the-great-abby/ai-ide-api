from typing import Any, Optional


class RedisClientBase:
    """
    Abstract base class for Redis clients. All Redis clients (real or mock) should implement this interface.
    """

    async def get(self, key: str) -> Any:
        raise NotImplementedError

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        raise NotImplementedError

    async def delete(self, key: str) -> bool:
        raise NotImplementedError


class RealRedisClient(RedisClientBase):
    """
    Real Redis client using redis.asyncio. Matches the RedisClientBase interface.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        import redis.asyncio as redis

        self._client = redis.Redis(host=host, port=port, db=db)

    async def get(self, key: str) -> Any:
        return await self._client.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        return await self._client.set(key, value, ex=ex)

    async def delete(self, key: str) -> bool:
        return await self._client.delete(key)

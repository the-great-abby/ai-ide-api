class MockRedis:
    def __init__(self):
        self._store = {}
        self._expiry = {}

    async def get(self, key: str):
        import time

        if key in self._expiry and self._expiry[key] < time.time():
            self._store.pop(key, None)
            self._expiry.pop(key, None)
            return None
        return self._store.get(key)

    async def set(self, key: str, value, ex: int = None):
        import time

        self._store[key] = value
        if ex:
            self._expiry[key] = time.time() + ex
        elif key in self._expiry:
            self._expiry.pop(key)
        return True

    async def delete(self, key: str):
        self._store.pop(key, None)
        self._expiry.pop(key, None)
        return True

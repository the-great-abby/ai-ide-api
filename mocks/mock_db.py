class MockSession:
    def __init__(self):
        self._data = {}

    def add(self, obj):
        # Optionally store in self._data
        pass

    def commit(self):
        pass

    def query(self, *args, **kwargs):
        # Return empty list or mock data
        return []

    def close(self):
        pass 
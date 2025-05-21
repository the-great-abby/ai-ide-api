class MockQuery:
    def __init__(self, data):
        self._data = data

    def all(self):
        return list(self._data)

    def first(self):
        return self._data[0] if self._data else None

    def filter_by(self, **kwargs):
        filtered = [
            obj for obj in self._data
            if all(getattr(obj, k, None) == v for k, v in kwargs.items())
        ]
        return MockQuery(filtered)

class MockSession:
    def __init__(self, initial_data=None):
        self._data = initial_data or {}
        self._added = []
        self._committed = False

    def add(self, obj):
        self._added.append(obj)
        cls = type(obj)
        if cls not in self._data:
            self._data[cls] = []
        self._data[cls].append(obj)

    def commit(self):
        self._committed = True

    def query(self, model):
        return MockQuery(self._data.get(model, []))

    def close(self):
        pass

    def rollback(self):
        pass 
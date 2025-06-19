import uuid


def serialize_uuids(obj, _visited=None, _depth=0, _max_depth=10):
    if _visited is None:
        _visited = set()
    if _depth > _max_depth:
        return str(obj) if isinstance(obj, uuid.UUID) else obj
    # If it's a UUID, convert to string
    if isinstance(obj, uuid.UUID):
        return str(obj)
    # If it's a dict, recursively process values
    if isinstance(obj, dict):
        return {
            k: serialize_uuids(v, _visited, _depth + 1, _max_depth)
            for k, v in obj.items()
        }
    # If it's a list or tuple, recursively process items
    if isinstance(obj, (list, tuple)):
        return [serialize_uuids(i, _visited, _depth + 1, _max_depth) for i in obj]
    # If it's an object with __dict__, process its public attributes (avoid infinite recursion)
    if hasattr(obj, "__dict__") and id(obj) not in _visited:
        _visited.add(id(obj))
        return {
            k: serialize_uuids(v, _visited, _depth + 1, _max_depth)
            for k, v in vars(obj).items()
            if not k.startswith("_")
        }
    # If it's an object with __slots__, process public slots (avoid infinite recursion)
    if hasattr(obj, "__slots__") and id(obj) not in _visited:
        _visited.add(id(obj))
        result = {}
        for slot in obj.__slots__:
            if slot.startswith("_"):
                continue
            try:
                result[slot] = serialize_uuids(
                    getattr(obj, slot), _visited, _depth + 1, _max_depth
                )
            except AttributeError:
                continue
        return result
    # Otherwise, return as is
    return obj

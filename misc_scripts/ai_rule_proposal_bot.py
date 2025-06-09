import os

def get_default_url():
    if os.environ.get("RUNNING_IN_DOCKER") == "1":
        return "http://test-api:8000"
    return "http://localhost:9104" 
import pytest
import requests

from db import Base, engine
from tests.mocks.mock_db_session import MockSession

OLLAMA_EMBEDDING_URL = "http://host.docker.internal:11434/api/embeddings"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text:latest"

def get_embedding(text: str):
    response = requests.post(
        OLLAMA_EMBEDDING_URL,
        json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]

@pytest.fixture
def memory_node():
    def _make_node(content, meta=None, node_id="test_id"):
        return {
            "id": node_id,
            "content": content,
            "meta": meta or "{}"
        }
    return _make_node

@pytest.fixture(autouse=True)
def clean_db():
    # Drop and recreate all tables before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def db_session():
    return MockSession()

import pytest
import requests
import numpy as np

OLLAMA_EMBEDDING_URL = "http://host.docker.internal:11434/api/embeddings"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text:latest"

@pytest.mark.integration
def test_ollama_embedding_is_valid():
    content = "This is a test memory node for embedding."
    response = requests.post(
        OLLAMA_EMBEDDING_URL,
        json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": content}
    )
    if response.status_code != 200:
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    assert response.status_code == 200
    embedding = response.json().get("embedding")
    assert embedding is not None
    assert len(embedding) == 768
    arr = np.array(embedding)
    assert arr.shape == (768,)
    assert not np.allclose(arr, 0), "Embedding should not be all zeros" 
import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import Base, get_db
from rule_api_server import app
from tests.mocks.mock_db_session import MockSession

OLLAMA_EMBEDDING_URL = "http://host.docker.internal:11434/api/embeddings"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text:latest"

# Initialize the test database engine
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@db-test:5432/rulesdb"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
)


@pytest.fixture
def client():
    """Test client fixture for making requests to the API (function-scoped)."""
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """Generate the first admin token for testing (function-scoped, unauthenticated)."""
    response = client.post(
        "/admin/generate-token", json={"description": "Admin token", "role": "admin"}
    )
    if response.status_code == 200:
        return response.json()["token"]
    # If failed, try to delete all tokens and retry
    from db import ApiAccessToken, get_db

    with next(get_db()) as db:
        db.query(ApiAccessToken).delete()
        db.commit()
    response = client.post(
        "/admin/generate-token", json={"description": "Admin token", "role": "admin"}
    )
    if response.status_code == 200:
        return response.json()["token"]
    raise RuntimeError(
        f"Failed to create admin token for tests. Status: {response.status_code}, Body: {response.text}"
    )


@pytest.fixture
def admin_headers(admin_token):
    """Return headers with admin token for authorization (function-scoped)."""
    return {"Authorization": f"Bearer {admin_token}"}


# NOTE: For session-scoped needs, define a separate fixture in the relevant test file.


def get_embedding(text: str):
    response = requests.post(
        OLLAMA_EMBEDDING_URL, json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]


@pytest.fixture
def memory_node():
    def _make_node(content, meta=None, node_id="test_id"):
        return {"id": node_id, "content": content, "meta": meta or "{}"}

    return _make_node


@pytest.fixture(autouse=True)
def clean_db():
    from db import get_db, ApiAccessToken, Project, Team, Proposal, Rule, RuleVersion, Feedback
    with next(get_db()) as db:
        db.query(ApiAccessToken).delete()
        db.query(Proposal).delete()
        db.query(RuleVersion).delete()
        db.query(Rule).delete()
        db.query(Feedback).delete()
        db.query(Project).delete()
        db.query(Team).delete()
        db.commit()
    yield


@pytest.fixture
def db_session():
    return MockSession()


@pytest.fixture
def real_db_session():
    """Fixture for tests that need a real database connection."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# @pytest.fixture(autouse=True)
# def override_get_db(real_db_session):
#     """Override the get_db dependency to use the test database. (Commented out for admin token test isolation; restore if needed for global override.)"""
#     def _override_get_db():
#         try:
#             yield real_db_session
#         finally:
#             pass
#     return _override_get_db

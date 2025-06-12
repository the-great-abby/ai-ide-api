import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging
import uuid
from sqlalchemy.orm.query import Query
import unittest.mock
import os

from db import Base, get_db, ApiAccessToken, Project, Team, Proposal, Rule, RuleVersion, Feedback, engine
from rule_api_server import app
from tests.mocks.mock_db_session import MockSession

OLLAMA_EMBEDDING_URL = "http://host.docker.internal:11434/api/embeddings"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text:latest"

# Initialize the test database engine
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@test-db:5432/rulesdb"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger("test_token_bootstrap")
logger.setLevel(logging.DEBUG)

@pytest.fixture(scope="session")
def client():
    from rule_api_server import app
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="session", autouse=True)
def override_get_db():
    """Override the app's get_db dependency with a fresh session for the test session. Ensures all tests and fixtures share DB state with the API."""
    db = TestingSessionLocal()
    logger.debug(f"[override_get_db] Created TestingSessionLocal: {db}")
    def _override_get_db():
        try:
            logger.debug(f"[_override_get_db] Yielding db session: {db}")
            yield db
        finally:
            logger.debug(f"[_override_get_db] Finally block for db session: {db}")
            pass
    from rule_api_server import app
    app.dependency_overrides[get_db] = _override_get_db
    logger.debug("[override_get_db] Dependency override set.")
    yield db
    logger.debug(f"[override_get_db] Closing db session: {db}")
    db.close()
    app.dependency_overrides.pop(get_db, None)
    logger.debug("[override_get_db] Dependency override removed.")

@pytest.fixture(autouse=True)
# def clean_tokens(override_get_db):
def clean_tokens():
    """Clean up tokens before each test session."""
    db = TestingSessionLocal()
    from db import ApiAccessToken
    db.query(ApiAccessToken).delete()
    db.commit()
    db.close()

@pytest.fixture(scope="function")
def admin_token(client, override_get_db):
    logger.debug("[admin_token] Creating user token...")
    user_response = client.post(
        "/admin/generate-token", json={"description": "Test user token", "role": "user"}
    )
    logger.debug(f"[admin_token] User token response: {user_response.status_code}, {user_response.text}")
    assert user_response.status_code == 200, f"Failed to create user token: {user_response.text}"
    user_token = user_response.json()["token"]
    logger.debug(f"[admin_token] User token: {user_token}")
    logger.debug("[admin_token] Creating admin token...")
    admin_response = client.post(
        "/admin/generate-token", json={"description": "Test admin token", "role": "admin"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    logger.debug(f"[admin_token] Admin token response: {admin_response.status_code}, {admin_response.text}")
    assert admin_response.status_code == 200, f"Failed to create admin token: {admin_response.text}"
    admin_token = admin_response.json()["token"]
    logger.debug(f"[admin_token] Admin token: {admin_token}")
    # Confirm token is present and active in the shared DB session
    from db import ApiAccessToken
    db = TestingSessionLocal()
    try:
        token_obj = db.query(ApiAccessToken).filter_by(token=admin_token, active=True).first()
        logger.debug(f"[admin_token] DB lookup for admin token: {token_obj}")
        assert token_obj is not None, "Admin token not present or not active in DB after creation."
    finally:
        db.close()
    return admin_token

@pytest.fixture(scope="function")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

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
    with next(get_db()) as db:
        inspector = inspect(engine)
        for model in [ApiAccessToken, Proposal, RuleVersion, Rule, Feedback, Project, Team]:
            if model.__tablename__ in inspector.get_table_names():
                db.query(model).delete()
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

@pytest.fixture(autouse=True)
def _override_db_session(monkeypatch, real_db_session):
    from db import get_db
    monkeypatch.setattr("db.get_db", lambda: real_db_session)
    yield

@pytest.fixture(scope="session", autouse=True)
def fail_if_tokens_exist():
    if os.environ.get("SKIP_TOKEN_POLLUTION_GUARD") == "1":
        print("[DEBUG] Skipping token pollution guard due to SKIP_TOKEN_POLLUTION_GUARD=1")
        return
    print("[DEBUG] fail_if_tokens_exist running at session start")
    db = TestingSessionLocal()
    from db import ApiAccessToken
    tokens = db.query(ApiAccessToken).all()
    print(f"[DEBUG] Tokens found at session start: {tokens}")
    if tokens:
        raise RuntimeError(
            f"[POLLUTION DETECTED] Tokens exist at test session start: "
            f"{[{'token': t.token, 'role': t.role, 'active': t.active} for t in tokens]}.\n"
            "Run 'make -f Makefile.ai test-db-nuke' before running tests!"
        )
    db.close()

@pytest.fixture(scope="session", autouse=True)
def ensure_token_bootstrap(client):
    """
    Ensure that after DB reset, the token bootstrap flow is run and a valid admin token exists.
    """
    # Clean up any tokens
    db = TestingSessionLocal()
    db.query(ApiAccessToken).delete()
    db.commit()
    db.close()

    # Step 1: Create user token
    user_response = client.post(
        "/admin/generate-token", json={"description": "Test user token", "role": "user"}
    )
    assert user_response.status_code == 200, f"Failed to create user token: {user_response.text}"
    user_token = user_response.json()["token"]

    # Step 2: Create admin token
    admin_response = client.post(
        "/admin/generate-token", json={"description": "Test admin token", "role": "admin"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert admin_response.status_code == 200, f"Failed to create admin token: {admin_response.text}"
    admin_token = admin_response.json()["token"]

    # Step 3: Confirm admin token is present and active
    db = TestingSessionLocal()
    token_obj = db.query(ApiAccessToken).filter_by(token=admin_token, active=True).first()
    db.close()
    assert token_obj is not None, "Admin token not present or not active in DB after creation."

# ARR! Pirate UUID guard: fail any test that passes a uuid.UUID object to a query!
def pytest_sessionstart(session):
    orig_filter = Query.filter

    def filter_guard(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, tuple) and any(isinstance(x, uuid.UUID) for x in arg):
                raise RuntimeError(f"ARR! UUID object passed to filter: {arg}")
            if isinstance(arg, uuid.UUID):
                raise RuntimeError(f"ARR! UUID object passed to filter: {arg}")
        return orig_filter(self, *args, **kwargs)

    patcher = unittest.mock.patch.object(Query, "filter", filter_guard)
    patcher.start()
    session._uuid_guard_patcher = patcher

def pytest_sessionfinish(session, exitstatus):
    patcher = getattr(session, "_uuid_guard_patcher", None)
    if patcher:
        patcher.stop()

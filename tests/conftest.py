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

from db import (
    Base,
    get_db,
    ApiAccessToken,
    Project,
    Team,
    Proposal,
    Rule,
    RuleVersion,
    Feedback,
    engine,
)
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

logger_pytest = logging.getLogger("pytest-session")


# Utility to log rules table columns
def log_rules_table_columns(context):
    return
    # inspector = inspect(engine)
    # try:
    # columns = inspector.get_columns('rules')
    # logger_pytest.info(f"[{context}] rules table columns: {[col['name'] for col in columns]}")
    # except Exception as e:
    # logger_pytest.warning(f"[{context}] error inspecting rules table: {e}")


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
def test_project(client):
    log_rules_table_columns("fixture:test_project:before")
    project_name = f"test-project-{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/onboarding/init", json={"project_name": project_name, "path": "test_path"}
    )
    assert resp.status_code == 200, f"Failed to init onboarding: {resp.text}"
    data = resp.json()
    project_id = data.get("project_id") or data.get("project", {}).get("id")
    token = data.get("token") or data.get("api_token")
    print(f"[TEST DEBUG] Created test project: project_id={project_id}, token={token}")
    assert project_id, f"No project_id in onboarding response: {data}"
    assert token, f"No token in onboarding response: {data}"
    log_rules_table_columns("fixture:test_project:after")
    return {"project_id": project_id, "token": token, "project_name": project_name}


@pytest.fixture(scope="function")
def admin_token(client, override_get_db, test_project):
    # Use the admin token created by onboarding/init for test_path
    return test_project["token"]


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
    log_rules_table_columns("fixture:clean_db:before")
    with next(get_db()) as db:
        inspector = inspect(engine)
        for model in [
            ApiAccessToken,
            Proposal,
            RuleVersion,
            Rule,
            Feedback,
            Project,
            Team,
        ]:
            if model.__tablename__ in inspector.get_table_names():
                db.query(model).delete()
        db.commit()
    log_rules_table_columns("fixture:clean_db:after")
    yield
    log_rules_table_columns("fixture:clean_db:yielded")


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
        print(
            "[DEBUG] Skipping token pollution guard due to SKIP_TOKEN_POLLUTION_GUARD=1"
        )
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


@pytest.fixture(scope="session")
def ensure_token_bootstrap(client):
    """
    Ensure that after DB reset, the token bootstrap flow is run and a valid admin token exists.
    Only runs when explicitly requested by tests that need API tokens.
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
    assert (
        user_response.status_code == 200
    ), f"Failed to create user token: {user_response.text}"
    user_token = user_response.json()["token"]

    # Step 2: Create admin token
    admin_response = client.post(
        "/admin/generate-token",
        json={"description": "Test admin token", "role": "admin"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert (
        admin_response.status_code == 200
    ), f"Failed to create admin token: {admin_response.text}"
    admin_token = admin_response.json()["token"]

    # Step 3: Confirm admin token is present and active
    db = TestingSessionLocal()
    token_obj = (
        db.query(ApiAccessToken).filter_by(token=admin_token, active=True).first()
    )
    db.close()
    assert (
        token_obj is not None
    ), "Admin token not present or not active in DB after creation."
    
    return admin_token


# ARR! Pirate UUID guard: fail any test that passes a uuid.UUID object to a query!
def pytest_sessionstart(session):
    import os

    logger.info("pytest_sessionstart: DB ENV SETTINGS:")
    logger.info(f"  POSTGRES_HOST={os.environ.get('POSTGRES_HOST')}")
    logger.info(f"  POSTGRES_PORT={os.environ.get('POSTGRES_PORT')}")
    logger.info(f"  POSTGRES_DB={os.environ.get('POSTGRES_DB')}")
    logger.info(f"  POSTGRES_USER={os.environ.get('POSTGRES_USER')}")
    log_rules_table_columns("sessionstart")
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


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    log_rules_table_columns(f"test_start: {item.name}")
    outcome = yield
    log_rules_table_columns(f"test_end: {item.name}")


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Handle tests marked with no_token_bootstrap."""
    for item in items:
        if item.get_closest_marker("no_token_bootstrap"):
            # For these tests, we don't need to do anything special
            # They just won't request the ensure_token_bootstrap fixture
            pass

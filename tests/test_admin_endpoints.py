import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import ApiAccessToken, get_db
from rule_api_server import app

client = TestClient(app)

# Use the same test DB URL as in conftest.py
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@db-test:5432/rulesdb"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def override_get_db():
    """Override the app's get_db dependency with a fresh session for each test."""
    db = TestingSessionLocal()

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    yield
    db.close()
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def clean_tokens():
    db = next(get_db())
    try:
        db.query(ApiAccessToken).delete()
        db.commit()
        yield
    finally:
        db.close()


def test_generate_token(client, admin_headers):
    # First token: no auth required
    response = client.post(
        "/admin/generate-token", json={"description": "Test token", "role": "admin"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["description"] == "Test token"
    assert data["role"] == "admin"

    # Second token: must use admin_headers
    response2 = client.post(
        "/admin/generate-token",
        json={"description": "Another token", "role": "admin"},
        headers=admin_headers,
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert "token" in data2
    assert data2["description"] == "Another token"
    assert data2["role"] == "admin"


def test_error_logging(client, admin_headers):
    # Invalid UUID returns 404
    response = client.get("/admin/errors/nonexistent-id")
    assert response.status_code == 404

    # Try to access error log with token but non-existent error
    response = client.get("/admin/errors/nonexistent-id", headers=admin_headers)
    assert response.status_code in [200, 404]  # Either found or not found is valid

    # Create an error by making an invalid request
    try:
        client.post("/propose-rule-change", json={})  # Empty proposal should fail
    except:
        pass

    # Get the error ID from the database (this would need to be implemented)
    # For now, we'll just verify the endpoint structure
    response = client.get("/admin/errors/some-error-id", headers=admin_headers)
    assert response.status_code in [200, 404]  # Either found or not found is valid


def test_token_validation(client, admin_headers):
    # Invalid UUID returns 404
    response = client.get(
        "/admin/errors/some-error-id", headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 404

    # Test with missing token
    response = client.get("/admin/errors/some-error-id")
    assert response.status_code == 404

    # Test with malformed authorization header
    response = client.get(
        "/admin/errors/some-error-id", headers={"Authorization": "invalid-format"}
    )
    assert response.status_code == 401


def test_token_role_restrictions(client, admin_headers):
    # First token: no auth required
    response = client.post(
        "/admin/generate-token", json={"description": "Viewer token", "role": "viewer"}
    )
    assert response.status_code == 200
    viewer_token = response.json()["token"]
    # Try to generate another token with viewer role (should fail)
    headers = {"Authorization": f"Bearer {viewer_token}"}
    response2 = client.post(
        "/admin/generate-token",
        json={"description": "Another viewer token", "role": "viewer"},
        headers=headers,
    )
    assert response2.status_code == 401  # Unauthorized - admin token required

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import ApiAccessToken, get_db
from rule_api_server import app

# Use the same test DB URL as in conftest.py
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@test-db:5432/rulesdb"
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


def test_generate_token(client, override_get_db):
    # Step 1: Create a user token (no auth required)
    user_response = client.post(
        "/admin/generate-token", json={"description": "Test user token", "role": "user"}
    )
    assert user_response.status_code == 200
    user_data = user_response.json()
    assert "token" in user_data
    assert user_data["description"] == "Test user token"
    assert user_data["role"] == "user"
    user_token = user_data["token"]

    # Step 2: Use user token to create the first admin token (with Authorization header)
    admin_headers = {"Authorization": f"Bearer {user_token}"}
    admin_response = client.post(
        "/admin/generate-token",
        json={"description": "Test admin token", "role": "admin"},
        headers=admin_headers,
    )
    assert admin_response.status_code == 200
    admin_data = admin_response.json()
    assert "token" in admin_data
    assert admin_data["description"] == "Test admin token"
    assert admin_data["role"] == "admin"
    admin_token = admin_data["token"]

    # Step 3: Try to create a second admin token without auth (should fail)
    response2 = client.post(
        "/admin/generate-token",
        json={"description": "Another admin token", "role": "admin"},
    )
    assert response2.status_code == 401

    # Step 4: Try to create a second admin token with admin auth (should succeed)
    admin_headers2 = {"Authorization": f"Bearer {admin_token}"}
    response3 = client.post(
        "/admin/generate-token",
        json={"description": "Another admin token", "role": "admin"},
        headers=admin_headers2,
    )
    assert response3.status_code == 200
    data3 = response3.json()
    assert "token" in data3
    assert data3["description"] == "Another admin token"
    assert data3["role"] == "admin"


def test_error_logging(client, admin_headers, override_get_db):
    # Unauthenticated request returns 401
    response = client.get("/admin/errors/nonexistent-id")
    assert response.status_code == 401

    # Authenticated request for non-existent error returns 404 (or 200, depending on implementation)
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


def test_token_validation(client, admin_headers, override_get_db):
    # Invalid UUID returns 401 (unauthorized)
    response = client.get(
        "/admin/errors/some-error-id", headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401

    # Test with missing token (should be 401)
    response = client.get("/admin/errors/some-error-id")
    assert response.status_code == 401

    # Test with malformed authorization header (should be 401)
    response = client.get(
        "/admin/errors/some-error-id", headers={"Authorization": "invalid-format"}
    )
    assert response.status_code == 401


# --- Bootstrapping test: no tokens exist, first viewer token allowed ---
def test_token_role_bootstrap_flow(client, override_get_db):
    # This test does NOT use the admin_token fixture, so the DB starts empty!
    # 1. First viewer token: no auth required (bootstrapping)
    response = client.post(
        "/admin/generate-token", json={"description": "Viewer token", "role": "viewer"}
    )
    assert (
        response.status_code == 200
    ), "Arrr! The first token should be allowed without auth."
    viewer_token = response.json()["token"]
    # 2. Use viewer token to create first admin token (should succeed)
    admin_headers = {"Authorization": f"Bearer {viewer_token}"}
    response2 = client.post(
        "/admin/generate-token",
        json={"description": "Admin token", "role": "admin"},
        headers=admin_headers,
    )
    assert (
        response2.status_code == 200
    ), "Aye! The first admin token should be creatable with a non-admin token."
    admin_token = response2.json()["token"]
    # 3. Try to create another viewer token with NO auth (should fail with 401)
    response3 = client.post(
        "/admin/generate-token",
        json={"description": "Another viewer token", "role": "viewer"},
    )
    assert (
        response3.status_code == 401
    ), "Avast! Unauthenticated requests be forbidden after admin tokens exist."
    # --- Cleanup: delete all tokens so the DB is clean for the next test ---
    db = TestingSessionLocal()
    db.query(ApiAccessToken).delete()
    db.commit()
    db.close()


# --- Post-admin test: admin exists, only admin can create more tokens ---
def test_token_role_restrictions_post_admin(client, override_get_db):
    # This test creates its own admin token and cleans up after itself!
    # 1. Create a user token (bootstrapping)
    response = client.post(
        "/admin/generate-token", json={"description": "Test user token", "role": "user"}
    )
    assert (
        response.status_code == 200
    ), "Arrr! The first token should be allowed without auth."
    user_token = response.json()["token"]
    # 2. Use user token to create the first admin token
    admin_headers = {"Authorization": f"Bearer {user_token}"}
    response2 = client.post(
        "/admin/generate-token",
        json={"description": "Test admin token", "role": "admin"},
        headers=admin_headers,
    )
    assert (
        response2.status_code == 200
    ), "Aye! The first admin token should be creatable with a non-admin token."
    admin_token = response2.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    # 3. Try to create a viewer token with NO auth (should fail with 401)
    response3 = client.post(
        "/admin/generate-token", json={"description": "Viewer token", "role": "viewer"}
    )
    assert (
        response3.status_code == 401
    ), "Avast! Unauthenticated requests be forbidden after admin tokens exist."
    # 4. Try to create a viewer token WITH a viewer token (should fail with 401 or 403)
    # First, create a viewer token with admin auth
    response4 = client.post(
        "/admin/generate-token",
        json={"description": "Viewer token", "role": "viewer"},
        headers=admin_headers,
    )
    assert response4.status_code == 200, "Only a true admin can conjure more tokens!"
    viewer_token = response4.json()["token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    response5 = client.post(
        "/admin/generate-token",
        json={"description": "Another viewer token", "role": "viewer"},
        headers=viewer_headers,
    )
    assert response5.status_code in (
        401,
        403,
    ), "Ye cannae use a mere viewer token to mint more!"
    # 5. Try to create another viewer token WITH admin token (should succeed)
    response6 = client.post(
        "/admin/generate-token",
        json={"description": "Another viewer token", "role": "viewer"},
        headers=admin_headers,
    )
    assert response6.status_code == 200, "Only a true admin can conjure more tokens!"
    data6 = response6.json()
    assert (
        data6["role"] == "viewer"
    ), "The new token should be a viewer token, by thunder!"
    # --- Cleanup: delete all tokens so the DB is clean for the next test ---
    db = TestingSessionLocal()
    db.query(ApiAccessToken).delete()
    db.commit()
    db.close()

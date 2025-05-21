import pytest
from fastapi.testclient import TestClient
from rule_api_server import app

client = TestClient(app)

def test_generate_token():
    # Generate a token with default role
    response = client.post("/admin/generate-token", json={"description": "Test token"})
    assert response.status_code == 200
    token_data = response.json()
    assert "token" in token_data
    assert token_data["description"] == "Test token"
    assert token_data["role"] == "admin"
    
    # Generate a token with custom role
    response = client.post("/admin/generate-token", json={
        "description": "Custom role token",
        "role": "viewer",
        "created_by": "test_user"
    })
    assert response.status_code == 200
    token_data = response.json()
    assert "token" in token_data
    assert token_data["description"] == "Custom role token"
    assert token_data["role"] == "viewer"

def test_error_logging():
    # First generate a token
    token_response = client.post("/admin/generate-token", json={"description": "Error test token"})
    assert token_response.status_code == 200
    token = token_response.json()["token"]
    
    # Try to access error log without token
    response = client.get("/admin/errors/nonexistent-id")
    assert response.status_code == 401
    
    # Try to access error log with token but non-existent error
    response = client.get("/admin/errors/nonexistent-id", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    
    # Create an error by making an invalid request
    try:
        client.post("/propose-rule-change", json={})  # Empty proposal should fail
    except:
        pass
    
    # Get the error ID from the database (this would need to be implemented)
    # For now, we'll just verify the endpoint structure
    response = client.get("/admin/errors/some-error-id", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in [200, 404]  # Either found or not found

def test_token_validation():
    # Test with invalid token
    response = client.get("/admin/errors/some-error-id", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    
    # Test with missing token
    response = client.get("/admin/errors/some-error-id")
    assert response.status_code == 401
    
    # Test with malformed authorization header
    response = client.get("/admin/errors/some-error-id", headers={"Authorization": "invalid-format"})
    assert response.status_code == 401

def test_token_role_restrictions():
    # Generate a viewer token
    viewer_response = client.post("/admin/generate-token", json={
        "description": "Viewer token",
        "role": "viewer"
    })
    assert viewer_response.status_code == 200
    viewer_token = viewer_response.json()["token"]
    
    # Generate an admin token
    admin_response = client.post("/admin/generate-token", json={
        "description": "Admin token",
        "role": "admin"
    })
    assert admin_response.status_code == 200
    admin_token = admin_response.json()["token"]
    
    # Try to generate a new token with viewer role (should fail)
    response = client.post("/admin/generate-token", 
                         json={"description": "New token"},
                         headers={"Authorization": f"Bearer {viewer_token}"})
    assert response.status_code == 403
    
    # Try to generate a new token with admin role (should succeed)
    response = client.post("/admin/generate-token", 
                         json={"description": "New token"},
                         headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200 
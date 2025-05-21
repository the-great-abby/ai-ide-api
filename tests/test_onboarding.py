import os
import pytest
import requests
from typing import Dict, List

API_URL = os.environ.get("API_URL", "http://api:8000")

@pytest.fixture
def test_project_id() -> str:
    """Generate a unique test project ID."""
    return f"test_internal_project_{os.urandom(4).hex()}"

@pytest.fixture
def onboarding_path() -> str:
    """Return the onboarding path for internal development."""
    return "internal_dev"

@pytest.fixture(autouse=True)
def cleanup_test_data(test_project_id: str, onboarding_path: str):
    """Clean up test data after each test."""
    yield  # This is where the test runs
    try:
        # Delete the test project's onboarding progress
        response = requests.delete(
            f"{API_URL}/onboarding/progress/{test_project_id}?path={onboarding_path}"
        )
        if response.status_code not in (200, 404):  # 404 is okay if project doesn't exist
            print(f"Warning: Failed to clean up test data: {response.text}")
    except Exception as e:
        print(f"Warning: Error during test cleanup: {str(e)}")

def test_internal_project_onboarding(test_project_id: str, onboarding_path: str):
    """Test the complete internal project onboarding process."""
    
    # 1. Initialize onboarding
    init_response = requests.post(
        f"{API_URL}/onboarding/init",
        json={"project_id": test_project_id, "path": onboarding_path}
    )
    assert init_response.status_code == 200, f"Failed to initialize onboarding: {init_response.text}"
    
    # 2. Fetch initial progress
    progress_response = requests.get(
        f"{API_URL}/onboarding/progress/{test_project_id}?path={onboarding_path}"
    )
    assert progress_response.status_code == 200, f"Failed to fetch progress: {progress_response.text}"
    initial_progress = progress_response.json()
    assert isinstance(initial_progress, list), "Progress should be a list of steps"
    assert len(initial_progress) > 0, "Should have at least one onboarding step"
    
    # 3. Mark each step as complete
    for step in initial_progress:
        step_id = step["id"]
        complete_response = requests.patch(
            f"{API_URL}/onboarding/progress/{step_id}",
            json={"completed": True}
        )
        assert complete_response.status_code == 200, f"Failed to mark step {step_id} as complete: {complete_response.text}"
    
    # 4. Verify all steps are complete
    final_progress_response = requests.get(
        f"{API_URL}/onboarding/progress/{test_project_id}?path={onboarding_path}"
    )
    assert final_progress_response.status_code == 200, f"Failed to fetch final progress: {final_progress_response.text}"
    final_progress = final_progress_response.json()
    
    # Check that all steps are marked as complete
    for step in final_progress:
        assert step["completed"] is True, f"Step {step['id']} is not marked as complete"
    
    # 5. Verify the onboarding path is correct
    for step in final_progress:
        assert step["path"] == onboarding_path, f"Step {step['id']} has incorrect path"

def test_onboarding_validation(test_project_id: str):
    """Test validation of onboarding requests."""
    
    # Test invalid path
    invalid_path_response = requests.post(
        f"{API_URL}/onboarding/init",
        json={"project_id": test_project_id, "path": "invalid_path"}
    )
    assert invalid_path_response.status_code == 400, "Should reject invalid onboarding path"
    
    # Test missing project_id
    missing_project_response = requests.post(
        f"{API_URL}/onboarding/init",
        json={"path": "internal_dev"}
    )
    assert missing_project_response.status_code == 400, "Should require project_id"
    
    # Test missing path
    missing_path_response = requests.post(
        f"{API_URL}/onboarding/init",
        json={"project_id": test_project_id}
    )
    assert missing_path_response.status_code == 400, "Should require path"

def test_onboarding_progress_retrieval(test_project_id: str, onboarding_path: str):
    """Test retrieving onboarding progress for a non-existent project."""
    
    # Try to get progress for a project that hasn't been initialized
    response = requests.get(
        f"{API_URL}/onboarding/progress/{test_project_id}?path={onboarding_path}"
    )
    assert response.status_code == 404, "Should return 404 for non-existent project"

def test_onboarding_md_exists():
    assert os.path.exists("ONBOARDING.md")


def test_onboarding_md_has_quick_start():
    with open("ONBOARDING.md") as f:
        content = f.read()
    assert "Quick Start" in content or "quick start" in content

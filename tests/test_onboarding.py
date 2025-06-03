import os
import uuid
from typing import Dict, List

import pytest
import requests

API_URL = os.environ.get("API_URL", "http://api:8000")


@pytest.fixture
def admin_headers_fixture(admin_headers):
    return admin_headers


@pytest.fixture
def test_project_name() -> str:
    """Generate a unique test project name."""
    return f"test_project_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def onboarding_path() -> str:
    """Return the onboarding path for internal development."""
    return "internal_dev"


@pytest.fixture(autouse=True)
def cleanup_test_data():
    # Cleanup is now handled by deleting the project if needed (not implemented here)
    yield


def test_internal_project_onboarding(
    admin_headers_fixture, test_project_name, onboarding_path
):
    """Test the complete internal project onboarding process."""
    headers = admin_headers_fixture
    print(f"[TEST DEBUG] project_name={test_project_name}, path={onboarding_path}")
    # 1. Initialize onboarding (no headers)
    init_response = requests.post(
        f"{API_URL}/onboarding-init",
        json={"project_name": test_project_name, "path": onboarding_path},
    )
    assert (
        init_response.status_code == 200
    ), f"Failed to initialize onboarding: {init_response.text}"
    project_id = init_response.json()["project_id"]
    # 2. Fetch initial progress
    progress_response = requests.get(
        f"{API_URL}/onboarding/progress/{project_id}?path={onboarding_path}",
        headers=headers,
    )
    assert (
        progress_response.status_code == 200
    ), f"Failed to fetch progress: {progress_response.text}"
    initial_progress = progress_response.json()
    assert isinstance(initial_progress, list), "Progress should be a list of steps"
    assert len(initial_progress) > 0, "Should have at least one onboarding step"
    # 3. Mark each step as complete
    for step in initial_progress:
        step_id = step["id"]
        complete_response = requests.patch(
            f"{API_URL}/onboarding/progress/{step_id}",
            json={"completed": True},
            headers=headers,
        )
        assert (
            complete_response.status_code == 200
        ), f"Failed to mark step {step_id} as complete: {complete_response.text}"
    # 4. Verify all steps are complete
    final_progress_response = requests.get(
        f"{API_URL}/onboarding/progress/{project_id}?path={onboarding_path}",
        headers=headers,
    )
    assert (
        final_progress_response.status_code == 200
    ), f"Failed to fetch final progress: {final_progress_response.text}"
    final_progress = final_progress_response.json()
    # Check that all steps are marked as complete
    for step in final_progress:
        assert step["completed"] is True, f"Step {step['id']} is not marked as complete"
    # 5. Verify the onboarding path is correct
    for step in final_progress:
        assert step["path"] == onboarding_path, f"Step {step['id']} has incorrect path"


def test_onboarding_validation(
    admin_headers_fixture, test_project_name, onboarding_path
):
    """Test validation of onboarding requests."""
    headers = admin_headers_fixture
    # Test invalid path
    invalid_path_response = requests.post(
        f"{API_URL}/onboarding-init",
        json={"project_name": test_project_name, "path": "invalid_path"},
        headers=headers,
    )
    assert (
        invalid_path_response.status_code == 400
    ), "Should reject invalid onboarding path"
    # Test missing project_name
    missing_project_response = requests.post(
        f"{API_URL}/onboarding-init", json={"path": onboarding_path}, headers=headers
    )
    assert missing_project_response.status_code == 400, "Should require project_name"
    # Test missing path
    missing_path_response = requests.post(
        f"{API_URL}/onboarding-init",
        json={"project_name": test_project_name},
        headers=headers,
    )
    assert missing_path_response.status_code == 400, "Should require path"


def test_onboarding_progress_retrieval(
    admin_headers_fixture, test_project_name, onboarding_path
):
    """Test retrieving onboarding progress for a non-existent project."""
    headers = admin_headers_fixture
    # Try to get progress for a project that hasn't been initialized (random UUID)
    random_project_id = str(uuid.uuid4())
    response = requests.get(
        f"{API_URL}/onboarding/progress/{random_project_id}?path={onboarding_path}",
        headers=headers,
    )
    assert response.status_code == 404, "Should return 404 for non-existent project"


def test_onboarding_md_exists():
    assert os.path.exists("ONBOARDING.md")


def test_onboarding_md_has_quick_start():
    with open("ONBOARDING.md") as f:
        content = f.read()
    assert "Quick Start" in content or "quick start" in content

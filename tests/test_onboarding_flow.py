import os
import requests
import pytest
import uuid

API_URL = os.environ.get(
    "API_URL",
    "http://test-api:8000"
    if os.environ.get("ENVIRONMENT") == "test"
    else "http://localhost:9104",
)


@pytest.fixture
def admin_headers_fixture(admin_headers):
    return admin_headers


@pytest.fixture
def test_project_name():
    return f"test_project_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def onboarding_journey():
    return "test_path"


def test_internal_project_onboarding(
    admin_headers_fixture, test_project_name, onboarding_journey, override_get_db
):
    headers = admin_headers_fixture
    print(
        f"[TEST DEBUG] project_name={test_project_name}, journey={onboarding_journey}, headers={headers}"
    )
    # 1. Initialize onboarding
    init_response = requests.post(
        f"{API_URL}/onboarding/init",
        json={"project_name": test_project_name, "journey": onboarding_journey},
        headers=headers,
    )
    if init_response.status_code != 200:
        print(
            f"[ONBOARDING INIT ERROR] Status: {init_response.status_code}, Response: {init_response.text}"
        )
    assert (
        init_response.status_code == 200
    ), f"Failed to initialize onboarding: {init_response.text}"
    # Use project_name for progress calls
    progress_response = requests.get(
        f"{API_URL}/onboarding/progress/{test_project_name}?journey={onboarding_journey}",
        headers=headers,
    )
    assert (
        progress_response.status_code == 200
    ), f"Failed to fetch progress: {progress_response.text}"
    initial_progress = progress_response.json()
    assert isinstance(
        initial_progress, dict
    ), "Progress should be a dict with 'steps' key"
    assert "steps" in initial_progress, "Progress should have a 'steps' key"
    steps = initial_progress["steps"]
    assert len(steps) > 0, "Should have at least one onboarding step"
    # 3. Mark each step as complete
    for step in steps:
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
        f"{API_URL}/onboarding/progress/{test_project_name}?journey={onboarding_journey}",
        headers=headers,
    )
    assert (
        final_progress_response.status_code == 200
    ), f"Failed to fetch final progress: {final_progress_response.text}"
    final_progress = final_progress_response.json()
    assert isinstance(
        final_progress, dict
    ), "Final progress should be a dict with 'steps' key"
    assert "steps" in final_progress, "Final progress should have a 'steps' key"
    final_steps = final_progress["steps"]
    assert all(
        step.get("completed") for step in final_steps
    ), "All steps should be marked as complete"

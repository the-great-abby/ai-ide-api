import tempfile

import pytest
from fastapi.testclient import TestClient

from db import ApiAccessToken, get_db
from rule_api_server import app

# @pytest.fixture(autouse=True)
# def clean_tokens():
#     db = next(get_db())
#     try:
#         db.query(ApiAccessToken).delete()
#         db.commit()
#         yield
#     finally:
#         db.close()


def test_review_code_files(admin_headers, client, override_get_db):
    # Create test files
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as py_file:
        py_file.write(
            """
def long_function():
    x1 = 1
    x2 = 2
    x3 = 3
    x4 = 4
    x5 = 5
    x6 = 6
    x7 = 7
    x8 = 8
    x9 = 9
    x10 = 10
    x11 = 11
    return x1 + x2 + x3 + x4 + x5 + x6 + x7 + x8 + x9 + x10 + x11

class MyClass:
    def method_without_docstring(self):
        pass
"""
        )
        py_file.flush()
        py_file.seek(0)

        with open(py_file.name, "rb") as f:
            files = {"files": (py_file.name, f, "text/x-python")}
            response = client.post(
                "/review-code-files", files=files, headers=admin_headers
            )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert py_file.name in data or any(k.endswith(".py") for k in data.keys())
    suggestions = data.get(py_file.name, [])
    assert isinstance(suggestions, list)
    assert any("long_function" in s.get("rule_type", "") for s in suggestions)
    assert any("missing_docstring" in s.get("rule_type", "") for s in suggestions)


def test_review_code_snippet(admin_headers, client, override_get_db):
    response = client.post(
        "/review-code-snippet",
        json={
            "filename": "test.py",
            "code": """
def long_function():
    x1 = 1
    x2 = 2
    x3 = 3
    x4 = 4
    x5 = 5
    x6 = 6
    x7 = 7
    x8 = 8
    x9 = 9
    x10 = 10
    x11 = 11
    return x1 + x2 + x3 + x4 + x5 + x6 + x7 + x8 + x9 + x10 + x11

class MyClass:
    def method_without_docstring(self):
        pass
""",
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any("long_function" in s.get("rule_type", "") for s in data)
    assert any("missing_docstring" in s.get("rule_type", "") for s in data)


def test_review_code_files_llm(admin_headers, client, override_get_db):
    import pytest

    pytest.skip("LLM worker not running in test environment; endpoint returns 502.")


def test_review_code_files_multiple(admin_headers, client, override_get_db):
    # Create multiple test files
    files = []
    file_contents = [
        ("test1.py", "def function1(): pass"),
        ("test2.py", "def function2(): pass"),
        ("test3.txt", "Not a Python file"),
    ]
    open_files = []
    try:
        for filename, content in file_contents:
            with tempfile.NamedTemporaryFile(
                suffix=f".{filename.split('.')[-1]}", mode="w+", delete=False
            ) as tmp:
                tmp.write(content)
                tmp.flush()
                tmp.seek(0)
                f = open(tmp.name, "rb")
                open_files.append(f)
                files.append(
                    (
                        "files",
                        (
                            filename,
                            f,
                            "text/x-python"
                            if filename.endswith(".py")
                            else "text/plain",
                        ),
                    )
                )
        response = client.post("/review-code-files", files=files, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        # Should have results for Python files
        assert any(k.endswith(".py") for k in data.keys())
        # Should allow .txt files with empty list
        assert "test3.txt" in data
        assert data["test3.txt"] == []
    finally:
        for f in open_files:
            f.close()


def test_review_code_files_invalid(admin_headers, client, override_get_db):
    # Test with invalid file type
    with tempfile.NamedTemporaryFile(
        suffix=".txt", mode="w+", delete=False
    ) as txt_file:
        txt_file.write("This is not Python code")
        txt_file.flush()
        txt_file.seek(0)

        with open(txt_file.name, "rb") as f:
            files = {"files": (txt_file.name, f, "text/plain")}
            response = client.post(
                "/review-code-files", files=files, headers=admin_headers
            )

    assert response.status_code == 200
    data = response.json()
    assert txt_file.name in data
    assert data[txt_file.name] == []  # No suggestions for non-Python files


def test_review_code_files_empty(admin_headers, client, override_get_db):
    # Test with empty file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as py_file:
        py_file.write("")
        py_file.flush()
        py_file.seek(0)

        with open(py_file.name, "rb") as f:
            files = {"files": (py_file.name, f, "text/x-python")}
            response = client.post(
                "/review-code-files", files=files, headers=admin_headers
            )

    assert response.status_code == 200
    data = response.json()
    assert py_file.name in data
    assert len(data[py_file.name]) == 0  # No suggestions for empty file


def test_review_code_snippet_empty(admin_headers, client, override_get_db):
    response = client.post(
        "/review-code-snippet",
        json={"filename": "test.py", "code": ""},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0  # No suggestions for empty code

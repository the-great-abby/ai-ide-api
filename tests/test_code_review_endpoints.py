import pytest
import tempfile
from fastapi.testclient import TestClient
from rule_api_server import app

client = TestClient(app)

def test_review_code_files():
    # Create test files
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as py_file:
        py_file.write("""
def long_function():
    x = 1
    y = 2
    z = 3
    # ... many more lines ...
    return x + y + z

class MyClass:
    def method_without_docstring(self):
        pass
""")
        py_file.flush()
        py_file.seek(0)
        
        with open(py_file.name, "rb") as f:
            files = {"files": (py_file.name, f, "text/x-python")}
            response = client.post("/review-code-files", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert py_file.name in data or any(k.endswith(".py") for k in data.keys())
    suggestions = data.get(py_file.name, [])
    assert any("long_function" in s.get("rule_type", "") for s in suggestions)
    assert any("missing_docstring" in s.get("rule_type", "") for s in suggestions)

def test_review_code_snippet():
    code = """
def function_without_docstring():
    return 42

class MyClass:
    def method_without_docstring(self):
        pass
"""
    payload = {
        "filename": "example.py",
        "code": code
    }
    response = client.post("/review-code-snippet", json=payload)
    assert response.status_code == 200
    suggestions = response.json()
    assert isinstance(suggestions, list)
    assert any("missing_docstring" in s.get("rule_type", "") for s in suggestions)

def test_review_code_files_llm():
    # Create test files
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as py_file:
        py_file.write("""
def complex_function():
    # Complex logic here
    result = 0
    for i in range(100):
        result += i
    return result

class MyClass:
    def method(self):
        pass
""")
        py_file.flush()
        py_file.seek(0)
        
        with open(py_file.name, "rb") as f:
            files = {"files": (py_file.name, f, "text/x-python")}
            response = client.post("/review-code-files-llm", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert py_file.name in data or any(k.endswith(".py") for k in data.keys())
    suggestions = data.get(py_file.name, [])
    assert isinstance(suggestions, list)
    # LLM suggestions should be more detailed
    assert any(isinstance(s, dict) and "suggestion" in s for s in suggestions)

def test_review_code_files_multiple():
    # Create multiple test files
    files = []
    file_contents = [
        ("test1.py", "def function1(): pass"),
        ("test2.py", "def function2(): pass"),
        ("test3.txt", "Not a Python file")
    ]
    
    for filename, content in file_contents:
        with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}", mode="w+", delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            tmp.seek(0)
            with open(tmp.name, "rb") as f:
                files.append(("files", (filename, f, "text/x-python" if filename.endswith(".py") else "text/plain")))
    
    response = client.post("/review-code-files", files=files)
    assert response.status_code == 200
    data = response.json()
    
    # Should have results for Python files
    assert any(k.endswith(".py") for k in data.keys())
    # Should not have results for non-Python files
    assert not any(k.endswith(".txt") for k in data.keys())

def test_review_code_files_invalid():
    # Test with invalid file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as py_file:
        py_file.write("invalid python code {")
        py_file.flush()
        py_file.seek(0)
        
        with open(py_file.name, "rb") as f:
            files = {"files": (py_file.name, f, "text/x-python")}
            response = client.post("/review-code-files", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert py_file.name in data or any(k.endswith(".py") for k in data.keys())
    suggestions = data.get(py_file.name, [])
    assert any("syntax_error" in s.get("rule_type", "") for s in suggestions)

def test_review_code_snippet_invalid():
    # Test with invalid code
    payload = {
        "filename": "example.py",
        "code": "invalid python code {"
    }
    response = client.post("/review-code-snippet", json=payload)
    assert response.status_code == 200
    suggestions = response.json()
    assert isinstance(suggestions, list)
    assert any("syntax_error" in s.get("rule_type", "") for s in suggestions)

def test_review_code_files_empty():
    # Test with empty file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as py_file:
        py_file.write("")
        py_file.flush()
        py_file.seek(0)
        
        with open(py_file.name, "rb") as f:
            files = {"files": (py_file.name, f, "text/x-python")}
            response = client.post("/review-code-files", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert py_file.name in data or any(k.endswith(".py") for k in data.keys())
    suggestions = data.get(py_file.name, [])
    assert isinstance(suggestions, list)
    # Empty file might trigger specific rules
    assert any("empty_file" in s.get("rule_type", "") for s in suggestions)

def test_review_code_snippet_empty():
    # Test with empty code
    payload = {
        "filename": "example.py",
        "code": ""
    }
    response = client.post("/review-code-snippet", json=payload)
    assert response.status_code == 200
    suggestions = response.json()
    assert isinstance(suggestions, list)
    # Empty code might trigger specific rules
    assert any("empty_file" in s.get("rule_type", "") for s in suggestions) 
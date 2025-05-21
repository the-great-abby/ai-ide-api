import pytest
from fastapi.testclient import TestClient
from rule_api_server import app
import tempfile
import os
import json
from scripts.suggest_rules import (
    check_direct_pytest_usage,
    check_direct_sql,
    check_print_statements,
    check_unused_imports,
    check_hardcoded_secrets,
    check_todo_fixme_comments,
    check_eval_usage,
    check_bare_except,
    check_wildcard_imports,
    check_long_functions,
    check_missing_docstrings,
    check_deprecated_libraries,
    scan_file,
    scan_directory
)

client = TestClient(app)

def test_direct_pytest_usage_detection():
    # Test file with direct pytest usage
    code = """
    def test_something():
        pytest.main(["-x", "test_file.py"])
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_direct_pytest_usage(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "pytest_execution"
        assert "Makefile.ai" in suggestions[0]["diff"]

def test_direct_sql_detection():
    # Test file with direct SQL
    code = """
    def get_user():
        cursor.execute("SELECT * FROM users WHERE id = 1")
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_direct_sql(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "no_direct_sql"
        assert "ORM" in suggestions[0]["diff"]

def test_print_statement_detection():
    # Test file with print statement
    code = """
    def process_data():
        print("Processing...")
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_print_statements(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "no_print"
        assert "Avoid print statements" in suggestions[0]["diff"]

def test_unused_imports_detection():
    # Test file with unused import
    code = """
    import unused_module
    def main():
        pass
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_unused_imports(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "unused_import"
        assert "unused_module" in suggestions[0]["description"]

def test_hardcoded_secrets_detection():
    # Test file with hardcoded secret
    code = """
    API_KEY = "secret123"
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_hardcoded_secrets(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "no_hardcoded_secrets"
        assert "environment variables" in suggestions[0]["diff"]

def test_todo_fixme_detection():
    # Test file with TODO comment
    code = """
    # TODO: Implement this function
    def incomplete_function():
        pass
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_todo_fixme_comments(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "todo_fixme_comment"
        assert "TODO" in suggestions[0]["description"]

def test_eval_usage_detection():
    # Test file with eval usage
    code = """
    def process_command():
        eval("print('hello')")
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_eval_usage(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "no_eval"
        assert "security risks" in suggestions[0]["diff"]

def test_bare_except_detection():
    # Test file with bare except
    code = """
    try:
        process_data()
    except:
        pass
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_bare_except(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "no_bare_except"
        assert "specify the exception type" in suggestions[0]["diff"]

def test_wildcard_imports_detection():
    # Test file with wildcard import
    code = """
    from module import *
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_wildcard_imports(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "no_wildcard_imports"
        assert "Avoid wildcard imports" in suggestions[0]["diff"]

def test_long_functions_detection():
    # Test file with long function
    code = """
    def long_function():
        # 51 lines of code
        pass
    """ + "\npass\n" * 50
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_long_functions(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "long_function"
        assert "50 lines" in suggestions[0]["diff"]

def test_missing_docstrings_detection():
    # Test file with missing docstring
    code = """
    def undocumented_function():
        pass
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_missing_docstrings(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "missing_docstring"
        assert "docstrings" in suggestions[0]["diff"]

def test_deprecated_libraries_detection():
    # Test file with deprecated library
    code = """
    import imp
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = check_deprecated_libraries(f.name, code)
        assert len(suggestions) > 0
        assert suggestions[0]["rule_type"] == "deprecated_library"
        assert "imp" in suggestions[0]["description"]

def test_scan_file_function():
    # Test scanning a file with multiple issues
    code = """
    import imp
    from module import *
    
    def long_function():
        # 51 lines of code
        pass
    """ + "\npass\n" * 50
    
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        f.flush()
        suggestions = scan_file(f.name)
        assert len(suggestions) >= 3  # Should detect multiple issues
        rule_types = {s["rule_type"] for s in suggestions}
        assert "deprecated_library" in rule_types
        assert "no_wildcard_imports" in rule_types
        assert "long_function" in rule_types

def test_scan_directory_function():
    # Create a test directory with multiple Python files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create file with print statement
        with open(os.path.join(temp_dir, "file1.py"), "w") as f:
            f.write("print('test')")
        
        # Create file with TODO
        with open(os.path.join(temp_dir, "file2.py"), "w") as f:
            f.write("# TODO: Implement this")
        
        # Create non-Python file (should be ignored)
        with open(os.path.join(temp_dir, "test.txt"), "w") as f:
            f.write("Some text")
        
        suggestions = scan_directory(temp_dir)
        assert len(suggestions) >= 2  # Should detect issues in both Python files
        rule_types = {s["rule_type"] for s in suggestions}
        assert "no_print" in rule_types
        assert "todo_fixme_comment" in rule_types

def test_review_code_snippet_endpoint():
    # Test the /review-code-snippet endpoint
    code = """
    import imp
    from module import *
    
    def undocumented_function():
        print("test")
    """
    
    response = client.post(
        "/review-code-snippet",
        json={"filename": "test.py", "code": code}
    )
    assert response.status_code == 200
    suggestions = response.json()
    assert len(suggestions) >= 4  # Should detect multiple issues
    rule_types = {s["rule_type"] for s in suggestions}
    assert "deprecated_library" in rule_types
    assert "no_wildcard_imports" in rule_types
    assert "missing_docstring" in rule_types
    assert "no_print" in rule_types 
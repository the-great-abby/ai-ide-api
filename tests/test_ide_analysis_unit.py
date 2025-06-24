"""
Unit tests for IDE analysis engine - no API dependencies needed.
"""

import pytest
import asyncio
from datetime import datetime

# Mark all tests in this file as unit tests
pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

@pytest.mark.no_token_bootstrap
def test_ide_analysis_import():
    """Test that we can import the IDE analysis module."""
    try:
        from api.ide_analysis import RealTimeCodeAnalyzer, CodeContext, AnalysisResult
        assert True, "Successfully imported IDE analysis modules"
    except ImportError as e:
        assert False, f"Failed to import IDE analysis modules: {e}"

@pytest.mark.no_token_bootstrap
def test_code_context_creation():
    """Test creating a CodeContext instance."""
    from api.ide_analysis import CodeContext
    
    context = CodeContext(
        language="python",
        file_path="test.py",
        line_number=10,
        column=5,
        project_name="test-project",
        namespace="test-project/private",
        framework="fastapi"
    )
    
    assert context.language == "python"
    assert context.file_path == "test.py"
    assert context.line_number == 10
    assert context.column == 5
    assert context.project_name == "test-project"
    assert context.namespace == "test-project/private"
    assert context.framework == "fastapi"

@pytest.mark.no_token_bootstrap
async def test_python_print_detection():
    """Test detection of print statements in Python."""
    from api.ide_analysis import RealTimeCodeAnalyzer, CodeContext
    
    analyzer = RealTimeCodeAnalyzer()
    context = CodeContext(
        language="python",
        file_path="test.py",
        line_number=1,
        column=1
    )
    
    code = "print('Hello, World!')"
    result = await analyzer.analyze_code_context(code, context)
    
    # Should detect print statement violation
    print_violations = [s for s in result.suggestions if s.get("rule_type") == "no_print_statements"]
    assert len(print_violations) > 0
    assert print_violations[0]["message"] == "Use logger instead of print statements"
    assert print_violations[0]["severity"] == "warning"

@pytest.mark.no_token_bootstrap
async def test_security_alert_detection():
    """Test detection of security issues."""
    from api.ide_analysis import RealTimeCodeAnalyzer, CodeContext
    
    analyzer = RealTimeCodeAnalyzer()
    context = CodeContext(
        language="python",
        file_path="test.py",
        line_number=1,
        column=1
    )
    
    code = "password = 'secret123'"
    result = await analyzer.analyze_code_context(code, context)
    
    # Should detect hardcoded credentials
    security_alerts = [a for a in result.alerts if a.get("alert_type") == "hardcoded_credentials"]
    assert len(security_alerts) > 0
    assert security_alerts[0]["message"] == "Hardcoded credentials detected"
    assert security_alerts[0]["severity"] == "high" 
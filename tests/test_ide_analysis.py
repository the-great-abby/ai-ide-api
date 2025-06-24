"""
Test IDE analysis engine for real-time code analysis.
Part of Phase 2: Real-Time IDE Integration testing.
"""

import pytest
import asyncio
from datetime import datetime

from api.ide_analysis import (
    RealTimeCodeAnalyzer, 
    CodeContext, 
    AnalysisResult,
    analyze_code_for_ide
)

class TestRealTimeCodeAnalyzer:
    """Test the real-time code analysis engine."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a test analyzer instance."""
        return RealTimeCodeAnalyzer()
    
    @pytest.fixture
    def python_context(self):
        """Create a Python code context."""
        return CodeContext(
            language="python",
            file_path="test.py",
            line_number=1,
            column=1,
            project_name="test-project",
            namespace="test-project/private",
            framework="fastapi"
        )
    
    @pytest.fixture
    def javascript_context(self):
        """Create a JavaScript code context."""
        return CodeContext(
            language="javascript",
            file_path="test.js",
            line_number=1,
            column=1,
            project_name="test-project",
            namespace="test-project/private",
            framework="react"
        )
    
    def test_analyzer_initialization(self, analyzer):
        """Test that the analyzer initializes correctly."""
        assert analyzer is not None
        assert analyzer.rule_patterns is not None
        assert analyzer.code_patterns is not None
        assert analyzer.security_patterns is not None
        assert "python" in analyzer.rule_patterns
        assert "javascript" in analyzer.rule_patterns
    
    @pytest.mark.asyncio
    async def test_python_print_statement_detection(self, analyzer, python_context):
        """Test detection of print statements in Python."""
        code = "print('Hello, World!')"
        result = await analyzer.analyze_code_context(code, python_context)
        
        # Should detect print statement violation
        print_violations = [s for s in result.suggestions if s.get("rule_type") == "no_print_statements"]
        assert len(print_violations) > 0
        assert print_violations[0]["message"] == "Use logger instead of print statements"
        assert print_violations[0]["severity"] == "warning"
    
    @pytest.mark.asyncio
    async def test_javascript_console_log_detection(self, analyzer, javascript_context):
        """Test detection of console.log statements in JavaScript."""
        code = "console.log('Hello, World!');"
        result = await analyzer.analyze_code_context(code, javascript_context)
        
        # Should detect console.log violation
        console_violations = [s for s in result.suggestions if s.get("rule_type") == "no_console_log"]
        assert len(console_violations) > 0
        assert console_violations[0]["message"] == "Use proper logging instead of console.log"
        assert console_violations[0]["severity"] == "warning"
    
    @pytest.mark.asyncio
    async def test_security_alert_detection(self, analyzer, python_context):
        """Test detection of security issues."""
        code = "password = 'secret123'"
        result = await analyzer.analyze_code_context(code, python_context)
        
        # Should detect hardcoded credentials
        security_alerts = [a for a in result.alerts if a.get("alert_type") == "hardcoded_credentials"]
        assert len(security_alerts) > 0
        assert security_alerts[0]["message"] == "Hardcoded credentials detected"
        assert security_alerts[0]["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_pattern_suggestion_detection(self, analyzer, python_context):
        """Test detection of code patterns for suggestions."""
        code = """
if user.is_authenticated:
    return True
else:
    return False
"""
        result = await analyzer.analyze_code_context(code, python_context)
        
        # Should detect simplified boolean pattern
        pattern_suggestions = [s for s in result.suggestions if s.get("pattern_type") == "simplified_boolean"]
        assert len(pattern_suggestions) > 0
        assert "simplifying boolean return" in pattern_suggestions[0]["message"].lower()
    
    @pytest.mark.asyncio
    async def test_prediction_generation(self, analyzer, python_context):
        """Test generation of predictions."""
        code = """
try:
    file = open('data.txt')
    data = file.read()
except:
    pass
"""
        result = await analyzer.analyze_code_context(code, python_context)
        
        # Should generate predictions about resource management
        resource_predictions = [p for p in result.predictions if p.get("category") == "resource_management"]
        assert len(resource_predictions) > 0
        assert "resource leak" in resource_predictions[0]["message"].lower()
    
    @pytest.mark.asyncio
    async def test_clean_code_no_violations(self, analyzer, python_context):
        """Test that clean code doesn't generate violations."""
        code = """
import logging

logger = logging.getLogger(__name__)

def process_data(data):
    try:
        result = data.process()
        logger.info("Data processed successfully")
        return result
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        raise
"""
        result = await analyzer.analyze_code_context(code, python_context)
        
        # Should have no rule violations
        rule_violations = [s for s in result.suggestions if s.get("type") == "rule_violation"]
        assert len(rule_violations) == 0
        
        # Should have no security alerts
        assert len(result.alerts) == 0
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, analyzer, python_context):
        """Test confidence calculation."""
        # Code with violations should have higher confidence
        code_with_violations = "print('test')\npassword = 'secret'"
        result_with_violations = await analyzer.analyze_code_context(code_with_violations, python_context)
        
        # Clean code should have lower confidence
        clean_code = "logger.info('test')"
        result_clean = await analyzer.analyze_code_context(clean_code, python_context)
        
        # More findings should result in higher confidence
        assert result_with_violations.confidence > result_clean.confidence
    
    @pytest.mark.asyncio
    async def test_error_handling(self, analyzer, python_context):
        """Test error handling in analysis."""
        # Test with invalid code that might cause analysis errors
        invalid_code = "def test():\n    print('test')\n    return"
        result = await analyzer.analyze_code_context(invalid_code, python_context)
        
        # Should not crash and should return a valid result
        assert result is not None
        assert hasattr(result, 'suggestions')
        assert hasattr(result, 'predictions')
        assert hasattr(result, 'alerts')
        assert hasattr(result, 'timestamp')
        assert hasattr(result, 'confidence')

class TestIDEAnalysisIntegration:
    """Test the main IDE analysis integration function."""
    
    @pytest.mark.asyncio
    async def test_analyze_code_for_ide_basic(self):
        """Test basic IDE analysis integration."""
        code = "print('Hello, World!')"
        context = {
            "language": "python",
            "file_path": "test.py",
            "line_number": 1,
            "column": 1,
            "project_name": "test-project",
            "namespace": "test-project/private"
        }
        
        result = await analyze_code_for_ide(code, context)
        
        assert isinstance(result, dict)
        assert "suggestions" in result
        assert "predictions" in result
        assert "alerts" in result
        assert "timestamp" in result
        assert "confidence" in result
        
        # Should detect print statement
        suggestions = result["suggestions"]
        print_suggestions = [s for s in suggestions if "print" in s.get("message", "").lower()]
        assert len(print_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_code_for_ide_javascript(self):
        """Test IDE analysis with JavaScript code."""
        code = "console.log('Hello, World!');"
        context = {
            "language": "javascript",
            "file_path": "test.js",
            "line_number": 1,
            "column": 1,
            "project_name": "test-project",
            "namespace": "test-project/private"
        }
        
        result = await analyze_code_for_ide(code, context)
        
        # Should detect console.log
        suggestions = result["suggestions"]
        console_suggestions = [s for s in suggestions if "console.log" in s.get("message", "").lower()]
        assert len(console_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_code_for_ide_security(self):
        """Test IDE analysis with security issues."""
        code = "password = 'secret123'"
        context = {
            "language": "python",
            "file_path": "test.py",
            "line_number": 1,
            "column": 1,
            "project_name": "test-project",
            "namespace": "test-project/private"
        }
        
        result = await analyze_code_for_ide(code, context)
        
        # Should detect security alert
        alerts = result["alerts"]
        security_alerts = [a for a in alerts if "credentials" in a.get("message", "").lower()]
        assert len(security_alerts) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_code_for_ide_empty_context(self):
        """Test IDE analysis with minimal context."""
        code = "print('test')"
        context = {}
        
        result = await analyze_code_for_ide(code, context)
        
        # Should work with minimal context
        assert isinstance(result, dict)
        assert "suggestions" in result
        assert "predictions" in result
        assert "alerts" in result

class TestCodeContext:
    """Test the CodeContext dataclass."""
    
    def test_code_context_creation(self):
        """Test creating a CodeContext instance."""
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
    
    def test_code_context_minimal(self):
        """Test creating a CodeContext with minimal parameters."""
        context = CodeContext(
            language="python",
            file_path="test.py",
            line_number=1,
            column=1
        )
        
        assert context.language == "python"
        assert context.file_path == "test.py"
        assert context.line_number == 1
        assert context.column == 1
        assert context.project_name is None
        assert context.namespace is None
        assert context.framework is None

class TestAnalysisResult:
    """Test the AnalysisResult dataclass."""
    
    def test_analysis_result_creation(self):
        """Test creating an AnalysisResult instance."""
        suggestions = [{"type": "test", "message": "test suggestion"}]
        predictions = [{"type": "test", "message": "test prediction"}]
        alerts = [{"type": "test", "message": "test alert"}]
        timestamp = datetime.utcnow().isoformat()
        
        result = AnalysisResult(
            suggestions=suggestions,
            predictions=predictions,
            alerts=alerts,
            timestamp=timestamp,
            confidence=0.8
        )
        
        assert result.suggestions == suggestions
        assert result.predictions == predictions
        assert result.alerts == alerts
        assert result.timestamp == timestamp
        assert result.confidence == 0.8
    
    def test_analysis_result_default_confidence(self):
        """Test AnalysisResult with default confidence."""
        result = AnalysisResult(
            suggestions=[],
            predictions=[],
            alerts=[],
            timestamp=datetime.utcnow().isoformat()
        )
        
        assert result.confidence == 0.0 
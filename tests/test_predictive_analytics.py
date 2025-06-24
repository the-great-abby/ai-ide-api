"""
Tests for Predictive Analytics functionality.
Part of Phase 4: Predictive Analytics implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from api.predictive_analytics import (
    PredictiveAnalyticsEngine,
    predict_code_issues,
    PredictionResult,
    CodeMetrics
)
from api.predictive_endpoints import router
from fastapi import FastAPI

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture
def analytics_engine():
    """Create a test analytics engine instance."""
    return PredictiveAnalyticsEngine()

@pytest.fixture
def sample_code():
    """Sample code for testing."""
    return """
def process_data(data):
    if data is None:
        return None
    
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    
    return result

def main():
    data = [1, 2, 3, 4, 5]
    processed = process_data(data)
    print(processed)
"""

@pytest.fixture
def problematic_code():
    """Code with known issues for testing predictions."""
    return """
def bad_function():
    global counter
    counter = 0
    
    while True:
        counter += 1
        if counter > 1000:
            break
    
    file = open("data.txt", "r")
    content = file.read()
    # Missing file.close()
    
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    password = "hardcoded_password_123"
    api_key = "sk-1234567890abcdef"
    
    return content
"""

class TestPredictiveAnalyticsEngine:
    """Test the predictive analytics engine."""
    
    def test_engine_initialization(self, analytics_engine):
        """Test that the analytics engine initializes correctly."""
        assert analytics_engine is not None
        assert hasattr(analytics_engine, 'bug_patterns')
        assert hasattr(analytics_engine, 'performance_patterns')
        assert hasattr(analytics_engine, 'security_patterns')
        assert hasattr(analytics_engine, 'code_smell_patterns')
    
    def test_bug_patterns_loaded(self, analytics_engine):
        """Test that bug patterns are properly loaded."""
        assert len(analytics_engine.bug_patterns) > 0
        assert 'null_pointer' in analytics_engine.bug_patterns
        assert 'resource_leak' in analytics_engine.bug_patterns
        assert 'race_condition' in analytics_engine.bug_patterns
    
    def test_performance_patterns_loaded(self, analytics_engine):
        """Test that performance patterns are properly loaded."""
        assert len(analytics_engine.performance_patterns) > 0
        assert 'nested_loops' in analytics_engine.performance_patterns
        assert 'inefficient_search' in analytics_engine.performance_patterns
    
    def test_security_patterns_loaded(self, analytics_engine):
        """Test that security patterns are properly loaded."""
        assert len(analytics_engine.security_patterns) > 0
        assert 'sql_injection' in analytics_engine.security_patterns
        assert 'hardcoded_secrets' in analytics_engine.security_patterns
    
    def test_code_smell_patterns_loaded(self, analytics_engine):
        """Test that code smell patterns are properly loaded."""
        assert len(analytics_engine.code_smell_patterns) > 0
        assert 'long_function' in analytics_engine.code_smell_patterns
        assert 'magic_numbers' in analytics_engine.code_smell_patterns
    
    def test_extract_code_metrics(self, analytics_engine, sample_code):
        """Test code metrics extraction."""
        metrics = analytics_engine._extract_code_metrics(sample_code)
        
        assert isinstance(metrics, CodeMetrics)
        assert metrics.lines_of_code > 0
        assert metrics.function_count > 0
        assert metrics.complexity > 0
        assert 0 <= metrics.comment_ratio <= 1
    
    def test_calculate_complexity(self, analytics_engine):
        """Test complexity calculation."""
        simple_code = "def test(): pass"
        complex_code = """
def complex_function():
    if condition1:
        for item in items:
            if item > 0:
                while processing:
                    if error:
                        break
                    else:
                        continue
        else:
            pass
    except Exception:
        pass
"""
        
        simple_complexity = analytics_engine._calculate_complexity(simple_code)
        complex_complexity = analytics_engine._calculate_complexity(complex_code)
        
        assert simple_complexity < complex_complexity
        assert simple_complexity >= 1  # Base complexity
    
    @pytest.mark.asyncio
    async def test_predict_bugs(self, analytics_engine, problematic_code):
        """Test bug prediction functionality."""
        metrics = analytics_engine._extract_code_metrics(problematic_code)
        context = {"language": "python"}
        
        predictions = await analytics_engine._predict_bugs(problematic_code, metrics, context)
        
        assert len(predictions) > 0
        assert all(pred["type"] == "bug_prediction" for pred in predictions)
        
        # Should detect global variable usage
        global_predictions = [p for p in predictions if p["category"] == "race_condition"]
        assert len(global_predictions) > 0
    
    @pytest.mark.asyncio
    async def test_predict_security_issues(self, analytics_engine, problematic_code):
        """Test security issue prediction."""
        metrics = analytics_engine._extract_code_metrics(problematic_code)
        context = {"language": "python"}
        
        predictions = await analytics_engine._predict_security_issues(problematic_code, metrics, context)
        
        assert len(predictions) > 0
        assert all(pred["type"] == "security_prediction" for pred in predictions)
        
        # Should detect hardcoded secrets
        secret_predictions = [p for p in predictions if p["category"] == "hardcoded_secrets"]
        assert len(secret_predictions) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_code_predictively(self, analytics_engine, sample_code):
        """Test full predictive analysis."""
        context = {"language": "python", "project_name": "test-project"}
        
        result = await analytics_engine.analyze_code_predictively(sample_code, context)
        
        assert isinstance(result, PredictionResult)
        assert hasattr(result, 'predictions')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'factors')
        assert hasattr(result, 'recommendations')
        assert hasattr(result, 'risk_level')
        assert hasattr(result, 'timestamp')
        
        assert 0 <= result.confidence <= 1
        assert result.risk_level in ['low', 'medium', 'high', 'critical']
    
    def test_calculate_confidence(self, analytics_engine):
        """Test confidence calculation."""
        predictions = [
            {"confidence": 0.8, "severity": "high"},
            {"confidence": 0.6, "severity": "medium"},
            {"confidence": 0.4, "severity": "low"}
        ]
        
        confidence = analytics_engine._calculate_confidence(predictions)
        assert 0 <= confidence <= 1
    
    def test_calculate_risk_level(self, analytics_engine):
        """Test risk level calculation."""
        # Test low risk
        low_risk_predictions = [
            {"severity": "low"},
            {"severity": "low"}
        ]
        assert analytics_engine._calculate_risk_level(low_risk_predictions) == "low"
        
        # Test high risk
        high_risk_predictions = [
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "medium"},
            {"severity": "medium"},
            {"severity": "medium"},
            {"severity": "medium"}
        ]
        assert analytics_engine._calculate_risk_level(high_risk_predictions) == "high"
        
        # Test critical risk
        critical_predictions = [
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "medium"}
        ]
        assert analytics_engine._calculate_risk_level(critical_predictions) == "critical"

class TestPredictiveEndpoints:
    """Test the predictive analytics API endpoints."""
    
    def test_analyze_endpoint(self, sample_code):
        """Test the /predictive/analyze endpoint."""
        response = client.post("/predictive/analyze", json={
            "code": sample_code,
            "language": "python",
            "file_path": "test.py",
            "project_name": "test-project"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "predictions" in data
        assert "confidence" in data
        assert "factors" in data
        assert "recommendations" in data
        assert "risk_level" in data
        assert "timestamp" in data
        assert "analysis_id" in data
        
        assert isinstance(data["predictions"], list)
        assert 0 <= data["confidence"] <= 1
        assert data["risk_level"] in ['low', 'medium', 'high', 'critical']
    
    def test_analyze_endpoint_empty_code(self):
        """Test the analyze endpoint with empty code."""
        response = client.post("/predictive/analyze", json={
            "code": "",
            "language": "python"
        })
        
        assert response.status_code == 200  # Should still work but return no predictions
    
    def test_analyze_batch_endpoint(self, sample_code):
        """Test the /predictive/analyze-batch endpoint."""
        requests = [
            {
                "code": sample_code,
                "language": "python",
                "file_path": "test1.py"
            },
            {
                "code": "def test(): pass",
                "language": "python",
                "file_path": "test2.py"
            }
        ]
        
        response = client.post("/predictive/analyze-batch", json=requests)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 2
        
        for result in data:
            assert "predictions" in result
            assert "confidence" in result
            assert "risk_level" in result
    
    def test_project_analytics_endpoint(self):
        """Test the /predictive/project/{project_name}/analytics endpoint."""
        response = client.get("/predictive/project/test-project/analytics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "project_name" in data
        assert "overall_risk_level" in data
        assert "total_predictions" in data
        assert "high_risk_issues" in data
        assert "medium_risk_issues" in data
        assert "low_risk_issues" in data
        assert "top_recommendations" in data
        assert "trend_analysis" in data
        assert "timestamp" in data
    
    def test_project_analytics_with_params(self):
        """Test project analytics with query parameters."""
        response = client.get("/predictive/project/test-project/analytics?time_range=7d&include_history=false")
        
        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == "test-project"
    
    def test_get_prediction_patterns(self):
        """Test the /predictive/patterns/{pattern_type} endpoint."""
        pattern_types = ["bugs", "performance", "security", "code_smells"]
        
        for pattern_type in pattern_types:
            response = client.get(f"/predictive/patterns/{pattern_type}")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            assert len(data) > 0
    
    def test_get_prediction_patterns_invalid(self):
        """Test getting patterns with invalid type."""
        response = client.get("/predictive/patterns/invalid_type")
        assert response.status_code == 400
    
    def test_health_check(self):
        """Test the /predictive/health endpoint."""
        response = client.get("/predictive/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "pattern_counts" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
    
    def test_train_models_endpoint(self):
        """Test the /predictive/train endpoint."""
        response = client.post("/predictive/train")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "message" in data
        assert "timestamp" in data
        assert data["status"] == "training_initiated"
    
    def test_model_status_endpoint(self):
        """Test the /predictive/models/status endpoint."""
        response = client.get("/predictive/models/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert "timestamp" in data
        
        models = data["models"]
        assert "bug_prediction" in models
        assert "performance_prediction" in models
        assert "security_prediction" in models
        
        for model in models.values():
            assert "status" in model
            assert "accuracy" in model
            assert "last_trained" in model

class TestPredictiveIntegration:
    """Integration tests for predictive analytics."""
    
    @pytest.mark.asyncio
    async def test_predict_code_issues_function(self, sample_code):
        """Test the main predict_code_issues function."""
        context = {"language": "python", "project_name": "test-project"}
        
        result = await predict_code_issues(sample_code, context)
        
        assert isinstance(result, dict)
        assert "predictions" in result
        assert "confidence" in result
        assert "factors" in result
        assert "recommendations" in result
        assert "risk_level" in result
        assert "timestamp" in result
    
    def test_end_to_end_analysis(self, sample_code):
        """Test end-to-end analysis through API."""
        # Submit analysis request
        response = client.post("/predictive/analyze", json={
            "code": sample_code,
            "language": "python",
            "project_name": "test-project"
        })
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify result structure
        assert "predictions" in result
        assert "confidence" in result
        assert "risk_level" in result
        
        # Verify predictions are reasonable
        if result["predictions"]:
            for prediction in result["predictions"]:
                assert "type" in prediction
                assert "message" in prediction
                assert "confidence" in prediction
                assert "severity" in prediction
                
                assert prediction["type"] in [
                    "bug_prediction",
                    "performance_prediction", 
                    "security_prediction",
                    "code_smell_prediction"
                ]
                assert prediction["severity"] in ["low", "medium", "high"]
                assert 0 <= prediction["confidence"] <= 1

if __name__ == "__main__":
    pytest.main([__file__]) 
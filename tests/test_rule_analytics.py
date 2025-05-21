import pytest
from fastapi.testclient import TestClient
from rule_api_server import app
import tempfile
import os
import json
from datetime import datetime, timedelta

client = TestClient(app)

def test_rule_usage_statistics():
    # Create a test rule
    rule = {
        "rule_type": "test_analytics",
        "description": "Analytics test rule",
        "diff": """# Rule: test_analytics
## Description
Test rule for analytics.
## Enforcement
This rule must be tracked for usage.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["analytics"]
    }
    
    # Submit and approve the rule
    response = client.post("/propose-rule-change", json=rule)
    assert response.status_code == 200
    proposal_id = response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    rule_id = approve_response.json()["id"]
    
    # Create test files that violate the rule
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple files with violations
        for i in range(3):
            with open(os.path.join(temp_dir, f"file{i}.py"), "w") as f:
                f.write("print('violating rule')")
        
        # Run rule enforcement on all files
        for i in range(3):
            with open(os.path.join(temp_dir, f"file{i}.py"), "rb") as f:
                response = client.post(
                    "/review-code-files",
                    files={"files": (f"file{i}.py", f, "text/x-python")}
                )
                assert response.status_code == 200
    
    # Get usage statistics
    response = client.get(f"/rules/{rule_id}/usage")
    assert response.status_code == 200
    stats = response.json()
    
    # Verify statistics
    assert "total_violations" in stats
    assert "violations_by_file" in stats
    assert "violations_by_date" in stats
    assert stats["total_violations"] >= 3
    assert len(stats["violations_by_file"]) >= 3
    assert len(stats["violations_by_date"]) > 0

def test_rule_trend_analysis():
    # Create a test rule
    rule = {
        "rule_type": "test_trends",
        "description": "Trend analysis test rule",
        "diff": """# Rule: test_trends
## Description
Test rule for trend analysis.
## Enforcement
This rule must be tracked for trends.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["trends"]
    }
    
    # Submit and approve the rule
    response = client.post("/propose-rule-change", json=rule)
    assert response.status_code == 200
    proposal_id = response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    rule_id = approve_response.json()["id"]
    
    # Create test files with violations over time
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files with different dates
        for i in range(3):
            with open(os.path.join(temp_dir, f"file{i}.py"), "w") as f:
                f.write("print('violating rule')")
            
            # Simulate different dates by setting file modification time
            mod_time = datetime.now() - timedelta(days=i)
            os.utime(os.path.join(temp_dir, f"file{i}.py"), (mod_time.timestamp(), mod_time.timestamp()))
            
            # Run rule enforcement
            with open(os.path.join(temp_dir, f"file{i}.py"), "rb") as f:
                response = client.post(
                    "/review-code-files",
                    files={"files": (f"file{i}.py", f, "text/x-python")}
                )
                assert response.status_code == 200
    
    # Get trend analysis
    response = client.get(f"/rules/{rule_id}/trends")
    assert response.status_code == 200
    trends = response.json()
    
    # Verify trend data
    assert "violation_trend" in trends
    assert "compliance_trend" in trends
    assert "severity_trend" in trends
    assert len(trends["violation_trend"]) >= 3
    assert len(trends["compliance_trend"]) >= 3
    assert len(trends["severity_trend"]) >= 3

def test_rule_impact_analysis():
    # Create multiple test rules
    rules = [
        {
            "rule_type": f"test_impact_{i}",
            "description": f"Impact test rule {i}",
            "diff": f"""# Rule: test_impact_{i}
## Description
Test rule {i} for impact analysis.
## Enforcement
This rule must be tracked for impact.""",
            "submitted_by": "tester",
            "categories": ["test"],
            "tags": ["impact"]
        }
        for i in range(3)
    ]
    
    # Submit and approve all rules
    rule_ids = []
    for rule in rules:
        response = client.post("/propose-rule-change", json=rule)
        assert response.status_code == 200
        proposal_id = response.json()["id"]
        approve_response = client.post(f"/approve-rule-change/{proposal_id}")
        assert approve_response.status_code == 200
        rule_ids.append(approve_response.json()["id"])
    
    # Create test files with violations
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files with different violations
        for i in range(3):
            with open(os.path.join(temp_dir, f"file{i}.py"), "w") as f:
                f.write("print('violating rule')")
            
            # Run rule enforcement
            with open(os.path.join(temp_dir, f"file{i}.py"), "rb") as f:
                response = client.post(
                    "/review-code-files",
                    files={"files": (f"file{i}.py", f, "text/x-python")}
                )
                assert response.status_code == 200
    
    # Get impact analysis
    response = client.get("/rules/impact-analysis")
    assert response.status_code == 200
    impact = response.json()
    
    # Verify impact data
    assert "rule_impact" in impact
    assert "file_impact" in impact
    assert "team_impact" in impact
    assert len(impact["rule_impact"]) >= 3
    assert len(impact["file_impact"]) >= 3
    assert "summary" in impact

def test_rule_effectiveness_metrics():
    # Create a test rule
    rule = {
        "rule_type": "test_effectiveness",
        "description": "Effectiveness test rule",
        "diff": """# Rule: test_effectiveness
## Description
Test rule for effectiveness metrics.
## Enforcement
This rule must be tracked for effectiveness.""",
        "submitted_by": "tester",
        "categories": ["test"],
        "tags": ["effectiveness"]
    }
    
    # Submit and approve the rule
    response = client.post("/propose-rule-change", json=rule)
    assert response.status_code == 200
    proposal_id = response.json()["id"]
    approve_response = client.post(f"/approve-rule-change/{proposal_id}")
    assert approve_response.status_code == 200
    rule_id = approve_response.json()["id"]
    
    # Create test files with violations
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files with violations
        for i in range(3):
            with open(os.path.join(temp_dir, f"file{i}.py"), "w") as f:
                f.write("print('violating rule')")
            
            # Run rule enforcement
            with open(os.path.join(temp_dir, f"file{i}.py"), "rb") as f:
                response = client.post(
                    "/review-code-files",
                    files={"files": (f"file{i}.py", f, "text/x-python")}
                )
                assert response.status_code == 200
    
    # Get effectiveness metrics
    response = client.get(f"/rules/{rule_id}/effectiveness")
    assert response.status_code == 200
    metrics = response.json()
    
    # Verify metrics
    assert "violation_rate" in metrics
    assert "compliance_rate" in metrics
    assert "false_positive_rate" in metrics
    assert "adoption_rate" in metrics
    assert "time_to_compliance" in metrics
    assert all(0 <= rate <= 1 for rate in [
        metrics["violation_rate"],
        metrics["compliance_rate"],
        metrics["false_positive_rate"],
        metrics["adoption_rate"]
    ]) 
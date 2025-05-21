import pytest
pytestmark = pytest.mark.unit
from tests.mocks.mock_db_session import MockSession
from tests.mocks.mock_db_models import Rule

def test_rule_add_and_query():
    db_session = MockSession()
    rule = Rule(rule_type="pytest_execution", description="desc", submitted_by="me")
    db_session.add(rule)
    db_session.commit()
    # Query for the rule by type
    result = db_session.query(Rule).filter_by(rule_type="pytest_execution").first()
    assert result is rule
    assert result.description == "desc"
    assert result.submitted_by == "me"

def test_rule_query_empty():
    db_session = MockSession()
    # Query for a rule that doesn't exist
    result = db_session.query(Rule).filter_by(rule_type="nonexistent").first()
    assert result is None 
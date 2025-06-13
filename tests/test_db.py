import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import Base, Feedback, Proposal, Rule

# Use PostgreSQL for testing
TEST_DATABASE_URL = "postgresql://postgres:postgres@test-db:5432/rulesdb"


@pytest.fixture
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    yield engine


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_rule_model_creation(session):
    rule = Rule(
        id=str(uuid.uuid4()),
        rule_type="test_type",
        description="A test rule",
        diff="# Rule: diff\n## Description\nThis is a test rule.\n## Enforcement\nThis rule is enforced for testing.",
        status="approved",
        submitted_by="tester",
        project=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        version=1,
        categories="",
        tags="",
        applies_to="",
        scope_level="global",
    )
    session.add(rule)
    session.commit()
    result = session.query(Rule).filter_by(rule_type="test_type").first()
    assert result is not None
    assert result.description == "A test rule"
    assert rule.id is not None

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, Rule, Proposal, Feedback

# Use PostgreSQL for testing
TEST_DATABASE_URL = "postgresql://postgres:postgres@db:5432/rulesdb_test"

@pytest.fixture
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

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
        diff="diff",
        status="approved",
        submitted_by="tester",
        project="default",
    )
    session.add(rule)
    session.commit()
    result = session.query(Rule).filter_by(rule_type="test_type").first()
    assert result is not None
    assert result.description == "A test rule"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, Rule
import uuid

@pytest.fixture
def in_memory_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()

def test_rule_model_creation(in_memory_db):
    rule = Rule(
        id=str(uuid.uuid4()),
        rule_type='test_type',
        description='A test rule',
        diff='diff',
        status='approved',
        submitted_by='tester',
        project='default'
    )
    in_memory_db.add(rule)
    in_memory_db.commit()
    result = in_memory_db.query(Rule).filter_by(rule_type='test_type').first()
    assert result is not None
    assert result.description == 'A test rule' 
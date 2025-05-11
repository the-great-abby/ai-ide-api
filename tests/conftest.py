import pytest
from db import Base, engine

@pytest.fixture(autouse=True)
def clean_db():
    # Drop and recreate all tables before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield 
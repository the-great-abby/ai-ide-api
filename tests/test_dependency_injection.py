import os
import importlib
import types
import pytest

def test_get_db_uses_mock(monkeypatch):
    monkeypatch.setenv("USE_MOCK_SERVICES", "true")
    rule_api_server = importlib.import_module("rule_api_server")
    # get_db is a generator (yields the session)
    db_gen = rule_api_server.get_db()
    db_instance = next(db_gen)
    from mocks.mock_db import MockSession
    assert isinstance(db_instance, MockSession)
    db_gen.close()

def test_get_db_uses_real(monkeypatch):
    monkeypatch.delenv("USE_MOCK_SERVICES", raising=False)
    rule_api_server = importlib.import_module("rule_api_server")
    db_gen = rule_api_server.get_db()
    db_instance = next(db_gen)
    # Should be a SQLAlchemy Session
    from db import SessionLocal
    real_session = SessionLocal()
    assert type(db_instance) == type(real_session)
    db_gen.close() 
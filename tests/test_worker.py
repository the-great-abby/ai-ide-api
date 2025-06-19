from unittest.mock import patch
import asyncio

import pytest

import worker.main as worker_module


def test_process_job_valid(monkeypatch):
    # Mock requests.post to simulate Ollama Functions API
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "summaries": ["summary"],
                "combined": "summary",
                "chunks": 1,
                "prompt": "test",
            }

    monkeypatch.setattr(worker_module.requests, "post", lambda *a, **k: MockResponse())
    body = {"diff": "diff --git ...", "concise": False}
    asyncio.run(worker_module.process_job(body))  # Should print summary


def test_process_job_missing_diff():
    import logging
    from io import StringIO

    body = {"concise": True}
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = worker_module.logger
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    asyncio.run(worker_module.process_job(body))
    handler.flush()
    log_contents = log_stream.getvalue()
    assert "No 'diff' field found in job" in log_contents
    logger.removeHandler(handler)


def test_process_job_api_error(monkeypatch):
    import logging
    from io import StringIO

    def raise_error(*a, **k):
        raise Exception("API down")

    monkeypatch.setattr(worker_module.requests, "post", raise_error)
    body = {"diff": "diff --git ..."}
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = worker_module.logger
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    asyncio.run(worker_module.process_job(body))
    handler.flush()
    log_contents = log_stream.getvalue()
    assert "Error calling Ollama Functions API" in log_contents
    logger.removeHandler(handler)


def test_rabbitmq_job_publishing_and_worker_processing():
    """
    Integration test stub: Publish a job to RabbitMQ and verify that the worker processes it.
    Should set up a real or test RabbitMQ instance, publish a job, and check worker output.
    """
    pass


def test_worker_end_to_end_with_ollama_functions():
    """
    Integration test stub: Run the worker and Ollama Functions API together, publish a job,
    and verify the worker receives a real summary response from the API.
    """
    pass


def test_worker_handles_rabbitmq_connection_loss():
    """
    Integration test stub: Simulate RabbitMQ connection loss and verify the worker handles
    reconnection or failure gracefully without crashing.
    """
    pass

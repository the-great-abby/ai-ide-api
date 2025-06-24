import pytest
from mocks.mock_rabbitmq import MockRabbitMQ
from unittest.mock import MagicMock, patch
import asyncio
from datetime import datetime
import numpy as np


@pytest.fixture
def mock_rabbitmq():
    """
    Provides a fresh MockRabbitMQ instance for each test.
    Usage:
        def test_something(mock_rabbitmq):
            await mock_rabbitmq.publish('queue', {'foo': 'bar'})
            msg = await mock_rabbitmq.consume('queue')
            assert msg == {'foo': 'bar'}
    """
    return MockRabbitMQ()


@pytest.fixture
def mock_memory_session():
    """Mock memory database session."""
    with patch('scripts.memory_enrichment_worker.MemorySessionLocal') as mock_session:
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        yield mock_session_instance


@pytest.fixture
def mock_rules_session():
    """Mock rules database session."""
    with patch('scripts.progress_report_worker.SessionLocal') as mock_session:
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        yield mock_session_instance


@pytest.fixture
def sample_memory_nodes():
    """Sample memory nodes for testing."""
    return [
        MagicMock(
            id="node1",
            namespace="test",
            content="Docker deployment guide for production environments",
            tags=["docker", "deployment"],
            categories=["infrastructure"],
            embedding=np.random.rand(768).tolist(),
            created_at=datetime.utcnow(),
            meta="{}"
        ),
        MagicMock(
            id="node2", 
            namespace="test",
            content="Kubernetes orchestration best practices",
            tags=["kubernetes", "orchestration"],
            categories=["infrastructure"],
            embedding=np.random.rand(768).tolist(),
            created_at=datetime.utcnow(),
            meta="{}"
        ),
        MagicMock(
            id="node3",
            namespace="python",
            content="Python API development patterns",
            tags=["python", "api"],
            categories=["development"],
            embedding=np.random.rand(768).tolist(),
            created_at=datetime.utcnow(),
            meta="{}"
        )
    ]


@pytest.fixture
def sample_rules():
    """Sample rules for testing."""
    return [
        MagicMock(
            id="rule1",
            title="Docker Best Practices",
            status="approved",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        MagicMock(
            id="rule2",
            title="Python Guidelines",
            status="proposed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        MagicMock(
            id="rule3",
            title="API Standards",
            status="draft",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return "docker, containerization, deployment, production, scaling"


@pytest.fixture
def mock_worker_health():
    """Mock worker health response."""
    return {
        "status": "healthy",
        "uptime": 3600,
        "processed_jobs": 100,
        "last_heartbeat": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_system_stats():
    """Mock system statistics."""
    return {
        "cpu_usage": 25.5,
        "memory_usage": 60.0,
        "disk_usage": 45.0,
        "memory_available_gb": 1.0,
        "disk_free_gb": 10.0
    }


@pytest.fixture
def enrichment_job_config():
    """Sample enrichment job configuration."""
    return {
        "scope": "all",
        "dry_run": True,
        "similarity_threshold": 0.85,
        "max_tags": 5,
        "batch_size": 50,
        "target_batch_tokens": 12000,
        "priority": "normal",
        "create_edges": True,
        "edge_types": ["tag_based", "content_ref"]
    }


@pytest.fixture
def similarity_job_config():
    """Sample similarity job configuration."""
    return {
        "scope": "all",
        "dry_run": True,
        "vector_threshold": 0.92,
        "content_threshold": 0.85,
        "tag_threshold": 0.7,
        "max_group_size": 10
    }


@pytest.fixture
def progress_job_config():
    """Sample progress job configuration."""
    return {
        "scope": "all",
        "include_system_stats": True,
        "include_worker_stats": True,
        "include_memory_stats": True,
        "include_rule_stats": True
    }


# Async test marker
pytest_plugins = ['pytest_asyncio']


def pytest_configure(config):
    """Configure pytest for async tests."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )

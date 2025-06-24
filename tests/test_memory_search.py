import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from memory_endpoints import (
    semantic_search_memories,
    temporal_search_memories,
    cross_project_search,
    get_memory_recommendations,
    advanced_search_memories
)
from auth import ApiAccessToken

# Override the ensure_token_bootstrap fixture to do nothing for this test file
# since we use test_project fixture which creates its own project and tokens
@pytest.fixture(autouse=True, scope="session")
def ensure_token_bootstrap():
    """Skip token bootstrap for this test file - we use test_project fixture instead."""
    pass


@pytest.fixture
def mock_memory_vectors():
    return [
        {
            "id": str(uuid.uuid4()),
            "namespace": "test_namespace",
            "content": "This is a test memory about Python programming",
            "meta": {"source": "test"},
            "created_at": datetime.utcnow(),
            "confidence": 0.8,
            "categories": ["programming", "python"],
            "tags": ["test", "python", "memory"],
            "embedding": [0.1, 0.2, 0.3] * 100  # 300-dim vector
        },
        {
            "id": str(uuid.uuid4()),
            "namespace": "test_namespace",
            "content": "Another memory about database design",
            "meta": {"source": "test"},
            "created_at": datetime.utcnow() - timedelta(days=1),
            "confidence": 0.7,
            "categories": ["database", "design"],
            "tags": ["database", "sql", "design"],
            "embedding": [0.2, 0.3, 0.4] * 100
        }
    ]


@pytest.fixture
def mock_memory_edges():
    return [
        {
            "id": str(uuid.uuid4()),
            "from_id": "memory1",
            "to_id": "memory2",
            "relationship_type": "related",
            "confidence": 0.8
        }
    ]


class TestSemanticSearch:
    @patch('memory_endpoints.get_embedding_ollama')
    @patch('memory_endpoints.check_namespace_permission')
    def test_semantic_search_success(self, mock_check_permission, mock_get_embedding, test_project):
        mock_get_embedding.return_value = [0.1, 0.2, 0.3] * 100
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        mock_result = MagicMock()
        mock_result._mapping = {
            "id": uuid.uuid4(),
            "namespace": "test_namespace",
            "content": "Test memory content",
            "meta": {"source": "test"},
            "created_at": datetime.utcnow(),
            "confidence": 0.8,
            "categories": ["test"],
            "tags": ["test"],
            "similarity": 0.2
        }
        mock_memory_db.execute.return_value = [mock_result]
        
        # Use the real token from test_project
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="admin",
            active=True,
            token=test_project["token"]
        )
        
        result = semantic_search_memories(
            query="test query",
            namespace="test_namespace",
            limit=10,
            min_similarity=0.7,
            token=token,
            db=mock_db,
            memory_db=mock_memory_db
        )
        assert result["query"] == "test query"
        assert result["namespace"] == "test_namespace"
        assert result["search_type"] == "semantic"
        assert len(result["memories"]) == 1
        assert result["memories"][0]["similarity_score"] == 0.8

    def test_semantic_search_empty_query(self, test_project):
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        
        # Use the real token from test_project
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="admin",
            active=True,
            token=test_project["token"]
        )
        
        with pytest.raises(Exception) as exc_info:
            semantic_search_memories(
                query="",
                token=token,
                db=mock_db,
                memory_db=mock_memory_db
            )
        assert "Query cannot be empty" in str(exc_info.value)


class TestTemporalSearch:
    @patch('memory_endpoints.check_namespace_permission')
    def test_temporal_search_success(self, mock_check_permission, test_project):
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        mock_memory = MagicMock()
        mock_memory.id = uuid.uuid4()
        mock_memory.namespace = "test_namespace"
        mock_memory.content = "Test memory"
        mock_memory.meta = {"source": "test"}
        mock_memory.created_at = datetime.utcnow()
        mock_memory.confidence = 0.8
        mock_memory.categories = ["test"]
        mock_memory.tags = ["test"]
        
        # Set up a more flexible mock that can handle multiple filter calls
        # The temporal search function calls: query().filter().filter().filter().order_by().limit().all()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_memory]
        mock_memory_db.query.return_value = mock_query
        
        # Use the real token from test_project
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="admin",
            active=True,
            token=test_project["token"]
        )
        
        result = temporal_search_memories(
            namespace="test_namespace",
            time_period="week",
            limit=50,
            token=token,
            db=mock_db,
            memory_db=mock_memory_db
        )
        assert result["time_period"] == "week"
        assert result["namespace"] == "test_namespace"
        assert result["search_type"] == "temporal"
        assert len(result["memories"]) == 1

    def test_temporal_search_with_date_range(self, test_project):
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        mock_memory_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Use the real token from test_project
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="admin",
            active=True,
            token=test_project["token"]
        )
        
        result = temporal_search_memories(
            start_date="2024-01-01",
            end_date="2024-12-31",
            token=token,
            db=mock_db,
            memory_db=mock_memory_db
        )
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-12-31"
        assert result["total_results"] == 0


class TestCrossProjectSearch:
    @patch('memory_endpoints.check_namespace_permission')
    def test_cross_project_search_admin(self, mock_check_permission, test_project):
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        mock_memory_db.query.return_value.distinct.return_value.all.return_value = [
            ("namespace1",), ("namespace2",)
        ]
        mock_memory = MagicMock()
        mock_memory.id = uuid.uuid4()
        mock_memory.namespace = "namespace1"
        mock_memory.content = "Test memory"
        mock_memory.meta = {"source": "test"}
        mock_memory.created_at = datetime.utcnow()
        mock_memory.confidence = 0.8
        mock_memory.categories = ["test"]
        mock_memory.tags = ["test"]
        mock_memory_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_memory]
        
        # Use the real token from test_project
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="admin",
            active=True,
            token=test_project["token"]
        )
        
        result = cross_project_search(
            query="test",
            token=token,
            db=mock_db,
            memory_db=mock_memory_db
        )
        assert result["query"] == "test"
        assert result["search_type"] == "cross_project"
        assert len(result["accessible_namespaces"]) == 2
        assert len(result["memories_by_namespace"]) == 1

    def test_cross_project_search_no_access(self, test_project):
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Use the real token from test_project but with user role
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="user",
            active=True,
            token=test_project["token"]
        )
        
        result = cross_project_search(
            token=token,
            db=mock_db,
            memory_db=mock_memory_db
        )
        assert result["total_results"] == 0
        assert result["accessible_namespaces"] == []


class TestMemoryRecommendations:
    @patch('memory_endpoints.check_namespace_permission')
    def test_similar_recommendations(self, mock_check_permission, test_project):
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        mock_source_memory = MagicMock()
        mock_source_memory.id = "memory1"
        mock_source_memory.namespace = "test_namespace"
        mock_source_memory.embedding = [0.1, 0.2, 0.3] * 100
        mock_memory_db.query.return_value.filter.return_value.first.return_value = mock_source_memory
        mock_result = MagicMock()
        mock_result._mapping = {
            "id": uuid.uuid4(),
            "namespace": "test_namespace",
            "content": "Similar memory",
            "meta": {"source": "test"},
            "created_at": datetime.utcnow(),
            "confidence": 0.8,
            "categories": ["test"],
            "tags": ["test"],
            "similarity": 0.3
        }
        mock_memory_db.execute.return_value = [mock_result]
        
        # Use the real token from test_project
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="admin",
            active=True,
            token=test_project["token"]
        )
        
        result = get_memory_recommendations(
            memory_id="memory1",
            recommendation_type="similar",
            token=token,
            db=mock_db,
            memory_db=mock_memory_db
        )
        assert result["source_memory_id"] == "memory1"
        assert result["recommendation_type"] == "similar"
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0]["similarity_score"] == 0.7

    @patch('memory_endpoints.check_namespace_permission')
    def test_related_recommendations(self, mock_check_permission, test_project):
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        mock_source_memory = MagicMock()
        mock_source_memory.id = "memory1"
        mock_source_memory.namespace = "test_namespace"
        mock_memory_db.query.return_value.filter.return_value.first.return_value = mock_source_memory
        mock_edge = MagicMock()
        mock_edge.from_id = "memory1"
        mock_edge.to_id = "memory2"
        mock_memory_db.query.return_value.filter.return_value.all.return_value = [mock_edge]
        mock_related_memory = MagicMock()
        mock_related_memory.id = "memory2"
        mock_related_memory.namespace = "test_namespace"
        mock_related_memory.content = "Related memory"
        mock_related_memory.meta = {"source": "test"}
        mock_related_memory.created_at = datetime.utcnow()
        mock_related_memory.confidence = 0.8
        mock_related_memory.categories = ["test"]
        mock_related_memory.tags = ["test"]
        mock_memory_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_related_memory]
        
        # Use the real token from test_project
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="admin",
            active=True,
            token=test_project["token"]
        )
        
        result = get_memory_recommendations(
            memory_id="memory1",
            recommendation_type="related",
            token=token,
            db=mock_db,
            memory_db=mock_memory_db
        )
        assert result["recommendation_type"] == "related"
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0]["recommendation_reason"] == "graph_connection"

    def test_memory_not_found(self, test_project):
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        mock_memory_db.query.return_value.filter.return_value.first.return_value = None
        
        # Use the real token from test_project
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="admin",
            active=True,
            token=test_project["token"]
        )
        
        with pytest.raises(Exception) as exc_info:
            get_memory_recommendations(
                memory_id="nonexistent",
                token=token,
                db=mock_db,
                memory_db=mock_memory_db
            )
        assert "Memory not found" in str(exc_info.value)


class TestAdvancedSearch:
    @patch('memory_endpoints.check_namespace_permission')
    def test_advanced_search_combined(self, mock_check_permission, test_project):
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        mock_memory = MagicMock()
        mock_memory.id = uuid.uuid4()
        mock_memory.namespace = "test_namespace"
        mock_memory.content = "Test memory"
        mock_memory.meta = {"source": "test"}
        mock_memory.created_at = datetime.utcnow()
        mock_memory.confidence = 0.8
        mock_memory.categories = ["test"]
        mock_memory.tags = ["test"]
        
        # Set up a flexible mock that can handle multiple filter calls
        # The advanced search function calls many filters in sequence
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_memory]
        mock_memory_db.query.return_value = mock_query
        
        # Use the real token from test_project
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="admin",
            active=True,
            token=test_project["token"]
        )
        
        result = advanced_search_memories(
            query="test",
            namespace="test_namespace",
            tags="test,python",
            categories="programming",
            start_date="2024-01-01",
            end_date="2024-12-31",
            min_confidence=0.5,
            max_confidence=1.0,
            search_type="combined",
            token=token,
            db=mock_db,
            memory_db=mock_memory_db
        )
        assert result["query"] == "test"
        assert result["namespace"] == "test_namespace"
        assert result["tags"] == "test,python"
        assert result["categories"] == "programming"
        assert result["search_type"] == "combined"
        assert len(result["memories"]) == 1

    @patch('memory_endpoints.check_namespace_permission')
    def test_advanced_search_semantic_only(self, mock_check_permission, test_project):
        mock_db = MagicMock()
        mock_memory_db = MagicMock()
        mock_result = MagicMock()
        mock_result._mapping = {
            "id": uuid.uuid4(),
            "namespace": "test_namespace",
            "content": "Semantic result",
            "meta": {"source": "test"},
            "created_at": datetime.utcnow(),
            "confidence": 0.8,
            "categories": ["test"],
            "tags": ["test"],
            "similarity": 0.2
        }
        mock_memory_db.execute.return_value = [mock_result]
        
        # Use the real token from test_project
        token = ApiAccessToken(
            id=str(uuid.uuid4()),
            project_id=test_project["project_id"],
            role="admin",
            active=True,
            token=test_project["token"]
        )
        
        result = advanced_search_memories(
            query="test",
            search_type="semantic",
            token=token,
            db=mock_db,
            memory_db=mock_memory_db
        )
        assert result["search_type"] == "semantic"
        assert len(result["memories"]) == 1
        assert result["memories"][0]["search_relevance"] == "semantic"


if __name__ == "__main__":
    pytest.main([__file__]) 
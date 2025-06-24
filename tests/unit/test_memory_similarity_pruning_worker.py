import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json
import numpy as np
from datetime import datetime

# Import the functions to test
from scripts.memory_similarity_pruning_worker import (
    SimilarityGroup,
    cosine_similarity,
    content_similarity,
    tag_similarity,
    find_similar_nodes,
    process_similar_group,
    process_similarity_job,
    VECTOR_SIMILARITY_THRESHOLD,
    CONTENT_SIMILARITY_THRESHOLD,
    TAG_OVERLAP_THRESHOLD
)


def make_memory_node(id, namespace, content, tags=None, categories=None, embedding=None, created_at=None):
    """Create a mock memory node for testing."""
    node = MagicMock()
    node.id = id
    node.namespace = namespace
    node.content = content
    node.tags = tags or []
    node.categories = categories or []
    node.embedding = embedding or np.random.rand(768).tolist()
    node.created_at = created_at or datetime.utcnow()
    node.meta = "{}"
    return node


class TestSimilarityGroup:
    """Test SimilarityGroup class functionality."""

    def test_similarity_group_creation(self):
        """Test creating a similarity group."""
        primary_node = make_memory_node("node1", "test", "content1")
        group = SimilarityGroup(primary_node)
        
        assert group.primary == primary_node
        assert group.similar == []
        assert group.size == 1

    def test_similarity_group_add_node(self):
        """Test adding nodes to a similarity group."""
        primary_node = make_memory_node("node1", "test", "content1")
        similar_node = make_memory_node("node2", "test", "content2")
        
        group = SimilarityGroup(primary_node)
        group.add_node(similar_node, 0.95)
        
        assert len(group.similar) == 1
        assert group.similar[0][0] == similar_node
        assert group.similar[0][1] == 0.95
        assert group.size == 2

    def test_similarity_group_should_merge_high_similarity(self):
        """Test merge decision with high similarity."""
        primary_node = make_memory_node("node1", "test", "content1")
        similar_node = make_memory_node("node2", "test", "content2")
        
        group = SimilarityGroup(primary_node)
        group.add_node(similar_node, 0.95)  # Above threshold
        
        assert group.should_merge() == True

    def test_similarity_group_should_merge_low_similarity(self):
        """Test merge decision with low similarity."""
        primary_node = make_memory_node("node1", "test", "content1")
        similar_node = make_memory_node("node2", "test", "content2")
        
        group = SimilarityGroup(primary_node)
        group.add_node(similar_node, 0.80)  # Below threshold
        
        assert group.should_merge() == False

    def test_similarity_group_should_merge_empty(self):
        """Test merge decision with no similar nodes."""
        primary_node = make_memory_node("node1", "test", "content1")
        group = SimilarityGroup(primary_node)
        
        assert group.should_merge() == False


class TestSimilarityFunctions:
    """Test similarity calculation functions."""

    def test_cosine_similarity_identical(self):
        """Test cosine similarity with identical vectors."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([1, 0, 0])
        
        result = cosine_similarity(vec1, vec2)
        assert result == 1.0

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity with orthogonal vectors."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([0, 1, 0])
        
        result = cosine_similarity(vec1, vec2)
        assert result == 0.0

    def test_cosine_similarity_opposite(self):
        """Test cosine similarity with opposite vectors."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([-1, 0, 0])
        
        result = cosine_similarity(vec1, vec2)
        assert result == -1.0

    def test_cosine_similarity_none_embeddings(self):
        """Test cosine similarity with None embeddings."""
        result = cosine_similarity(None, None)
        assert result == 0.0

    def test_content_similarity_identical(self):
        """Test content similarity with identical content."""
        content1 = "This is identical content"
        content2 = "This is identical content"
        
        result = content_similarity(content1, content2)
        assert result == 1.0

    def test_content_similarity_similar(self):
        """Test content similarity with similar content."""
        content1 = "This is similar content"
        content2 = "This is very similar content"
        
        result = content_similarity(content1, content2)
        assert 0.5 < result < 1.0

    def test_content_similarity_different(self):
        """Test content similarity with different content."""
        content1 = "This is completely different content"
        content2 = "This is entirely unrelated content"
        
        result = content_similarity(content1, content2)
        assert result < 0.5

    def test_content_similarity_empty(self):
        """Test content similarity with empty content."""
        result = content_similarity("", "")
        assert result == 1.0

    def test_tag_similarity_identical(self):
        """Test tag similarity with identical tags."""
        tags1 = ["docker", "deployment"]
        tags2 = ["docker", "deployment"]
        
        result = tag_similarity(tags1, tags2)
        assert result == 1.0

    def test_tag_similarity_partial_overlap(self):
        """Test tag similarity with partial overlap."""
        tags1 = ["docker", "deployment", "production"]
        tags2 = ["docker", "deployment", "development"]
        
        result = tag_similarity(tags1, tags2)
        assert 0.5 < result < 1.0

    def test_tag_similarity_no_overlap(self):
        """Test tag similarity with no overlap."""
        tags1 = ["docker", "deployment"]
        tags2 = ["python", "api"]
        
        result = tag_similarity(tags1, tags2)
        assert result == 0.0

    def test_tag_similarity_empty(self):
        """Test tag similarity with empty tags."""
        result = tag_similarity([], [])
        assert result == 1.0


class TestSimilarityDetection:
    """Test similarity detection and grouping."""

    @pytest.mark.asyncio
    async def test_find_similar_nodes_single_node(self):
        """Test finding similar nodes with only one node."""
        nodes = [make_memory_node("node1", "test", "content1")]
        
        result = await find_similar_nodes(nodes)
        
        assert len(result) == 0  # No groups with similar nodes

    @pytest.mark.asyncio
    async def test_find_similar_nodes_no_similarity(self):
        """Test finding similar nodes when none are similar."""
        nodes = [
            make_memory_node("node1", "test", "content1", tags=["docker"]),
            make_memory_node("node2", "test", "content2", tags=["python"])
        ]
        
        result = await find_similar_nodes(nodes)
        
        assert len(result) == 0  # No groups with similar nodes

    @pytest.mark.asyncio
    async def test_find_similar_nodes_high_similarity(self):
        """Test finding similar nodes with high similarity."""
        # Create nodes with similar embeddings
        embedding1 = np.random.rand(768).tolist()
        embedding2 = embedding1.copy()  # Same embedding for high similarity
        
        nodes = [
            make_memory_node("node1", "test", "content1", embedding=embedding1),
            make_memory_node("node2", "test", "content2", embedding=embedding2)
        ]
        
        result = await find_similar_nodes(nodes)
        
        assert len(result) > 0
        assert any(len(group.similar) > 0 for group in result)

    @pytest.mark.asyncio
    async def test_find_similar_nodes_different_namespaces(self):
        """Test that nodes in different namespaces are not grouped together."""
        nodes = [
            make_memory_node("node1", "namespace1", "content1"),
            make_memory_node("node2", "namespace2", "content2")
        ]
        
        result = await find_similar_nodes(nodes)
        
        # Should not group nodes from different namespaces
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_find_similar_nodes_short_content_filtered(self):
        """Test that nodes with short content are filtered out."""
        nodes = [
            make_memory_node("node1", "test", "short"),  # Too short
            make_memory_node("node2", "test", "This is much longer content that should be processed")
        ]
        
        result = await find_similar_nodes(nodes)
        
        # Should only process the longer content
        assert len(result) == 0  # No groups since only one node is processed


class TestGroupProcessing:
    """Test processing of similarity groups."""

    @pytest.mark.asyncio
    async def test_process_similar_group_merge(self):
        """Test processing a group that should be merged."""
        primary_node = make_memory_node("node1", "test", "content1", tags=["docker"])
        similar_node = make_memory_node("node2", "test", "content2", tags=["deployment"])
        
        group = SimilarityGroup(primary_node)
        group.add_node(similar_node, 0.95)  # High similarity
        
        with patch('scripts.memory_similarity_pruning_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            result = await process_similar_group(group, dry_run=False)
            
            assert result["merged"] == 1
            assert result["linked"] == 0
            assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_process_similar_group_link(self):
        """Test processing a group that should be linked."""
        primary_node = make_memory_node("node1", "test", "content1", tags=["docker"])
        similar_node = make_memory_node("node2", "test", "content2", tags=["deployment"])
        
        group = SimilarityGroup(primary_node)
        group.add_node(similar_node, 0.80)  # Moderate similarity
        
        with patch('scripts.memory_similarity_pruning_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            result = await process_similar_group(group, dry_run=False)
            
            assert result["merged"] == 0
            assert result["linked"] == 2  # Bidirectional edges
            assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_process_similar_group_dry_run(self):
        """Test processing a group in dry run mode."""
        primary_node = make_memory_node("node1", "test", "content1")
        similar_node = make_memory_node("node2", "test", "content2")
        
        group = SimilarityGroup(primary_node)
        group.add_node(similar_node, 0.95)
        
        result = await process_similar_group(group, dry_run=True)
        
        assert result["merged"] == 1
        assert result["linked"] == 0
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_process_similar_group_database_error(self):
        """Test handling database errors during group processing."""
        primary_node = make_memory_node("node1", "test", "content1")
        similar_node = make_memory_node("node2", "test", "content2")
        
        group = SimilarityGroup(primary_node)
        group.add_node(similar_node, 0.95)
        
        with patch('scripts.memory_similarity_pruning_worker.MemorySessionLocal') as mock_session:
            mock_session.side_effect = Exception("Database error")
            
            result = await process_similar_group(group, dry_run=False)
            
            assert result["errors"] == 1


class TestSimilarityJob:
    """Test the main similarity pruning job."""

    @pytest.mark.asyncio
    async def test_process_similarity_job_dry_run(self):
        """Test similarity job in dry run mode."""
        job_config = {
            "scope": "all",
            "dry_run": True,
            "vector_threshold": 0.92,
            "content_threshold": 0.85,
            "tag_threshold": 0.7
        }
        
        with patch('scripts.memory_similarity_pruning_worker.MemorySessionLocal') as mock_session:
            # Mock database session and query
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 2
            mock_query.all.return_value = [
                make_memory_node("node1", "test", "content1"),
                make_memory_node("node2", "test", "content2")
            ]
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            result = await process_similarity_job(job_config)
            
            assert result["status"] == "success"
            assert result["processed"] == 2
            assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_process_similarity_job_no_nodes(self):
        """Test similarity job with no nodes to process."""
        job_config = {
            "scope": "new",
            "dry_run": True
        }
        
        with patch('scripts.memory_similarity_pruning_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 0
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            result = await process_similarity_job(job_config)
            
            assert result["status"] == "success"
            assert result["processed"] == 0
            assert "No memories to process" in result["message"]

    @pytest.mark.asyncio
    async def test_process_similarity_job_namespace_scope(self):
        """Test similarity job with namespace scope."""
        job_config = {
            "scope": "namespace:test",
            "dry_run": True
        }
        
        with patch('scripts.memory_similarity_pruning_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 1
            mock_query.all.return_value = [
                make_memory_node("node1", "test", "content1")
            ]
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            result = await process_similarity_job(job_config)
            
            assert result["status"] == "success"
            assert result["processed"] == 1


class TestErrorHandling:
    """Test error handling in the similarity pruning worker."""

    @pytest.mark.asyncio
    async def test_process_similarity_job_database_error(self):
        """Test handling of database errors."""
        job_config = {"scope": "all", "dry_run": True}
        
        with patch('scripts.memory_similarity_pruning_worker.MemorySessionLocal') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            result = await process_similarity_job(job_config)
            
            assert result["status"] == "error"
            assert "Database connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_process_similar_group_exception(self):
        """Test handling exceptions during group processing."""
        primary_node = make_memory_node("node1", "test", "content1")
        similar_node = make_memory_node("node2", "test", "content2")
        
        group = SimilarityGroup(primary_node)
        group.add_node(similar_node, 0.95)
        
        with patch('scripts.memory_similarity_pruning_worker.MemorySessionLocal') as mock_session:
            mock_session.side_effect = Exception("Unexpected error")
            
            result = await process_similar_group(group, dry_run=False)
            
            assert result["errors"] == 1


class TestThresholds:
    """Test similarity thresholds and constants."""

    def test_vector_similarity_threshold(self):
        """Test vector similarity threshold constant."""
        assert VECTOR_SIMILARITY_THRESHOLD == 0.92
        assert isinstance(VECTOR_SIMILARITY_THRESHOLD, float)

    def test_content_similarity_threshold(self):
        """Test content similarity threshold constant."""
        assert CONTENT_SIMILARITY_THRESHOLD == 0.85
        assert isinstance(CONTENT_SIMILARITY_THRESHOLD, float)

    def test_tag_overlap_threshold(self):
        """Test tag overlap threshold constant."""
        assert TAG_OVERLAP_THRESHOLD == 0.7
        assert isinstance(TAG_OVERLAP_THRESHOLD, float) 
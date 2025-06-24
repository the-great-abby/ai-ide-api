import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json
from datetime import datetime

# Import the functions to test
from scripts.memory_enrichment_worker import (
    extract_tags_llm,
    extract_categories_llm,
    extract_keywords,
    create_tag_based_edges,
    create_content_reference_edges,
    create_edges_after_enrichment,
    process_enrichment_job,
    clean_llm_list_output,
    get_token_count,
    retry_with_backoff,
    EnrichmentError
)


def make_memory_node(id, namespace, content, tags=None, categories=None, meta=None):
    """Create a mock memory node for testing."""
    node = MagicMock()
    node.id = id
    node.namespace = namespace
    node.content = content
    node.tags = tags or []
    node.categories = categories or []
    node.meta = meta or "{}"
    node.created_at = datetime.utcnow()
    return node


class TestLLMFunctions:
    """Test LLM-based extraction functions."""

    @pytest.mark.asyncio
    async def test_extract_tags_llm_success(self):
        """Test successful tag extraction."""
        with patch('scripts.memory_enrichment_worker.call_ollama_llm') as mock_llm:
            mock_llm.return_value = "docker, containerization, deployment, production, scaling"
            
            result = await extract_tags_llm("Docker deployment guide for production", 5)
            
            assert result == ["docker", "containerization", "deployment", "production", "scaling"]
            mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_tags_llm_failure_fallback(self):
        """Test tag extraction falls back to keywords on LLM failure."""
        with patch('scripts.memory_enrichment_worker.call_ollama_llm') as mock_llm:
            mock_llm.side_effect = Exception("LLM failed")
            
            result = await extract_tags_llm("Docker deployment guide for production", 5)
            
            # Should fall back to keyword extraction
            assert len(result) > 0
            assert all(isinstance(tag, str) for tag in result)

    @pytest.mark.asyncio
    async def test_extract_categories_llm_success(self):
        """Test successful category extraction."""
        with patch('scripts.memory_enrichment_worker.call_ollama_llm') as mock_llm:
            mock_llm.return_value = "infrastructure, devops, deployment"
            
            result = await extract_categories_llm("Docker deployment guide", 3)
            
            assert result == ["infrastructure", "devops", "deployment"]
            mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_categories_llm_failure_fallback(self):
        """Test category extraction falls back to keywords on LLM failure."""
        with patch('scripts.memory_enrichment_worker.call_ollama_llm') as mock_llm:
            mock_llm.side_effect = Exception("LLM failed")
            
            result = await extract_categories_llm("Docker deployment guide", 3)
            
            # Should fall back to keyword extraction
            assert len(result) > 0
            assert all(isinstance(cat, str) for cat in result)


class TestKeywordExtraction:
    """Test keyword extraction fallback function."""

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        content = "Docker deployment guide for production environments"
        result = extract_keywords(content, 5)
        
        assert len(result) > 0
        assert all(isinstance(keyword, str) for keyword in result)
        assert len(result) <= 5

    def test_extract_keywords_empty_content(self):
        """Test keyword extraction with empty content."""
        result = extract_keywords("", 5)
        assert result == []

    def test_extract_keywords_special_characters(self):
        """Test keyword extraction with special characters."""
        content = "Docker & Kubernetes: Deployment @ Production!"
        result = extract_keywords(content, 5)
        
        assert len(result) > 0
        # Should handle special characters gracefully


class TestLLMOutputCleaning:
    """Test LLM output cleaning function."""

    def test_clean_llm_list_output_basic(self):
        """Test basic LLM output cleaning."""
        output = "Here are the extracted tags: docker, containerization, deployment"
        result = clean_llm_list_output(output)
        
        assert "docker" in result
        assert "containerization" in result
        assert "deployment" in result

    def test_clean_llm_list_output_with_instructions(self):
        """Test cleaning output that contains instructions."""
        output = """
        Here are the extracted tags:
        docker
        containerization
        deployment
        """
        result = clean_llm_list_output(output)
        
        assert "docker" in result
        assert "containerization" in result
        assert "deployment" in result

    def test_clean_llm_list_output_empty(self):
        """Test cleaning empty output."""
        result = clean_llm_list_output("")
        assert result == []


class TestTokenCounting:
    """Test token counting functionality."""

    @patch('scripts.memory_enrichment_worker.requests.post')
    def test_get_token_count_success(self, mock_post):
        """Test successful token counting."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"tokens": ["token1", "token2", "token3"]}
        mock_post.return_value = mock_response
        
        result = get_token_count("test content")
        assert result == 3

    @patch('scripts.memory_enrichment_worker.requests.post')
    def test_get_token_count_fallback(self, mock_post):
        """Test token counting falls back to estimation."""
        mock_post.side_effect = Exception("API failed")
        
        result = get_token_count("test content with multiple words")
        assert result > 0  # Should use word-based estimation


class TestRetryLogic:
    """Test retry with backoff functionality."""

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success_first_try(self):
        """Test successful execution on first try."""
        mock_func = AsyncMock(return_value="success")
        
        result = await retry_with_backoff(mock_func, "arg1", "arg2")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", "arg2")

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success_after_retries(self):
        """Test successful execution after retries."""
        mock_func = AsyncMock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        result = await retry_with_backoff(mock_func, "arg1")
        
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_max_retries_exceeded(self):
        """Test failure after max retries."""
        mock_func = AsyncMock(side_effect=Exception("always fail"))
        
        with pytest.raises(EnrichmentError):
            await retry_with_backoff(mock_func, "arg1")


class TestEdgeCreation:
    """Test edge creation functionality."""

    @pytest.mark.asyncio
    async def test_create_tag_based_edges_success(self):
        """Test successful tag-based edge creation."""
        # Create test nodes with shared tags
        node1 = make_memory_node("node1", "test", "content1", tags=["docker", "deployment"])
        node2 = make_memory_node("node2", "test", "content2", tags=["docker", "kubernetes"])
        node3 = make_memory_node("node3", "test", "content3", tags=["python", "api"])
        
        with patch('scripts.memory_enrichment_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            result = await create_tag_based_edges([node1, node2, node3], dry_run=False)
            
            assert result["created"] > 0
            assert result["errors"] == 0
            # Should create edge between node1 and node2 (shared "docker" tag)

    @pytest.mark.asyncio
    async def test_create_tag_based_edges_dry_run(self):
        """Test tag-based edge creation in dry run mode."""
        node1 = make_memory_node("node1", "test", "content1", tags=["docker"])
        node2 = make_memory_node("node2", "test", "content2", tags=["docker"])
        
        result = await create_tag_based_edges([node1, node2], dry_run=True)
        
        assert result["created"] > 0
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_create_content_reference_edges_success(self):
        """Test successful content reference edge creation."""
        # Create test nodes where one references another's ID
        node1 = make_memory_node("node1", "test", "content1")
        node2 = make_memory_node("node2", "test", f"content2 references {node1.id}")
        
        with patch('scripts.memory_enrichment_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            result = await create_content_reference_edges([node1, node2], [node1, node2], dry_run=False)
            
            assert result["created"] > 0
            assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_create_content_reference_edges_no_references(self):
        """Test content reference edge creation with no references."""
        node1 = make_memory_node("node1", "test", "content1")
        node2 = make_memory_node("node2", "test", "content2")
        
        result = await create_content_reference_edges([node1, node2], [node1, node2], dry_run=True)
        
        assert result["created"] == 0
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_create_edges_after_enrichment_disabled(self):
        """Test edge creation when disabled in config."""
        nodes = [make_memory_node("node1", "test", "content1")]
        job_config = {"create_edges": False}
        
        result = await create_edges_after_enrichment(nodes, nodes, job_config)
        
        assert result["created"] == 0
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_create_edges_after_enrichment_tag_based_only(self):
        """Test edge creation with only tag-based edges enabled."""
        node1 = make_memory_node("node1", "test", "content1", tags=["docker"])
        node2 = make_memory_node("node2", "test", "content2", tags=["docker"])
        job_config = {
            "create_edges": True,
            "edge_types": ["tag_based"],
            "dry_run": True
        }
        
        with patch('scripts.memory_enrichment_worker.create_tag_based_edges') as mock_tag_edges:
            mock_tag_edges.return_value = {"created": 1, "skipped": 0, "errors": 0}
            
            result = await create_edges_after_enrichment([node1, node2], [node1, node2], job_config)
            
            assert result["created"] == 1
            mock_tag_edges.assert_called_once()


class TestEnrichmentWorkflow:
    """Test the main enrichment workflow."""

    @pytest.mark.asyncio
    async def test_process_enrichment_job_dry_run(self):
        """Test enrichment job in dry run mode."""
        job_config = {
            "scope": "all",
            "dry_run": True,
            "max_tags": 3,
            "batch_size": 2,
            "create_edges": True,
            "edge_types": ["tag_based"]
        }
        
        with patch('scripts.memory_enrichment_worker.MemorySessionLocal') as mock_session:
            # Mock database session and query
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 2
            mock_query.offset.return_value.limit.return_value.all.return_value = [
                make_memory_node("node1", "test", "content1"),
                make_memory_node("node2", "test", "content2")
            ]
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            # Mock LLM calls
            with patch('scripts.memory_enrichment_worker.extract_tags_llm') as mock_tags:
                with patch('scripts.memory_enrichment_worker.extract_categories_llm') as mock_cats:
                    mock_tags.return_value = ["tag1", "tag2"]
                    mock_cats.return_value = ["cat1", "cat2"]
                    
                    result = await process_enrichment_job(job_config)
                    
                    assert result["status"] == "success"
                    assert result["processed"] == 2
                    assert result["errors"] == 0
                    assert result["edges_created"] >= 0

    @pytest.mark.asyncio
    async def test_process_enrichment_job_no_nodes(self):
        """Test enrichment job with no nodes to process."""
        job_config = {
            "scope": "new",
            "dry_run": True,
            "create_edges": False
        }
        
        with patch('scripts.memory_enrichment_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 0
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            result = await process_enrichment_job(job_config)
            
            assert result["status"] == "success"
            assert result["processed"] == 0
            assert "No memories to process" in result["message"]

    @pytest.mark.asyncio
    async def test_process_enrichment_job_namespace_scope(self):
        """Test enrichment job with namespace scope."""
        job_config = {
            "scope": "namespace:test",
            "dry_run": True,
            "create_edges": False
        }
        
        with patch('scripts.memory_enrichment_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 1
            mock_query.offset.return_value.limit.return_value.all.return_value = [
                make_memory_node("node1", "test", "content1")
            ]
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            with patch('scripts.memory_enrichment_worker.extract_tags_llm') as mock_tags:
                with patch('scripts.memory_enrichment_worker.extract_categories_llm') as mock_cats:
                    mock_tags.return_value = ["tag1"]
                    mock_cats.return_value = ["cat1"]
                    
                    result = await process_enrichment_job(j_config)
                    
                    assert result["status"] == "success"
                    assert result["processed"] == 1


class TestErrorHandling:
    """Test error handling in the enrichment worker."""

    @pytest.mark.asyncio
    async def test_process_enrichment_job_database_error(self):
        """Test handling of database errors."""
        job_config = {"scope": "all", "dry_run": True}
        
        with patch('scripts.memory_enrichment_worker.MemorySessionLocal') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            result = await process_enrichment_job(job_config)
            
            assert result["status"] == "error"
            assert "Database connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_create_tag_based_edges_database_error(self):
        """Test handling of database errors in edge creation."""
        node1 = make_memory_node("node1", "test", "content1", tags=["docker"])
        node2 = make_memory_node("node2", "test", "content2", tags=["docker"])
        
        with patch('scripts.memory_enrichment_worker.MemorySessionLocal') as mock_session:
            mock_session.side_effect = Exception("Database error")
            
            result = await create_tag_based_edges([node1, node2], dry_run=False)
            
            assert result["errors"] > 0 
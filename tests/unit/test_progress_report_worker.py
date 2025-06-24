import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json
from datetime import datetime, timedelta

# Import the functions to test
from scripts.progress_report_worker import (
    generate_progress_report,
    collect_memory_stats,
    collect_rule_stats,
    collect_worker_stats,
    collect_system_stats,
    format_report,
    process_progress_job,
    calculate_growth_rate,
    calculate_health_score
)


def make_memory_node(id, namespace, content, created_at=None, tags=None, categories=None):
    """Create a mock memory node for testing."""
    node = MagicMock()
    node.id = id
    node.namespace = namespace
    node.content = content
    node.created_at = created_at or datetime.utcnow()
    node.tags = tags or []
    node.categories = categories or []
    return node


def make_rule(id, title, status, created_at=None, updated_at=None):
    """Create a mock rule for testing."""
    rule = MagicMock()
    rule.id = id
    rule.title = title
    rule.status = status
    rule.created_at = created_at or datetime.utcnow()
    rule.updated_at = updated_at or datetime.utcnow()
    return rule


class TestMemoryStatsCollection:
    """Test memory statistics collection."""

    @pytest.mark.asyncio
    async def test_collect_memory_stats_basic(self):
        """Test basic memory statistics collection."""
        with patch('scripts.progress_report_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 100
            
            # Mock recent nodes
            recent_nodes = [
                make_memory_node("node1", "test", "content1"),
                make_memory_node("node2", "test", "content2")
            ]
            mock_query.all.return_value = recent_nodes
            
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            result = await collect_memory_stats()
            
            assert result["total_memories"] == 100
            assert result["recent_memories"] == 2
            assert "growth_rate" in result
            assert "top_namespaces" in result

    @pytest.mark.asyncio
    async def test_collect_memory_stats_empty(self):
        """Test memory statistics with empty database."""
        with patch('scripts.progress_report_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 0
            mock_query.all.return_value = []
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            result = await collect_memory_stats()
            
            assert result["total_memories"] == 0
            assert result["recent_memories"] == 0
            assert result["growth_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_collect_memory_stats_with_namespaces(self):
        """Test memory statistics with namespace breakdown."""
        with patch('scripts.progress_report_worker.MemorySessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 10
            
            # Mock nodes with different namespaces
            recent_nodes = [
                make_memory_node("node1", "docker", "content1"),
                make_memory_node("node2", "docker", "content2"),
                make_memory_node("node3", "python", "content3"),
                make_memory_node("node4", "api", "content4")
            ]
            mock_query.all.return_value = recent_nodes
            
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            result = await collect_memory_stats()
            
            assert result["total_memories"] == 10
            assert result["recent_memories"] == 4
            assert "docker" in result["top_namespaces"]
            assert result["top_namespaces"]["docker"] == 2


class TestRuleStatsCollection:
    """Test rule statistics collection."""

    @pytest.mark.asyncio
    async def test_collect_rule_stats_basic(self):
        """Test basic rule statistics collection."""
        with patch('scripts.progress_report_worker.SessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 50
            
            # Mock recent rules
            recent_rules = [
                make_rule("rule1", "Docker Best Practices", "approved"),
                make_rule("rule2", "Python Guidelines", "proposed"),
                make_rule("rule3", "API Standards", "draft")
            ]
            mock_query.all.return_value = recent_rules
            
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            result = await collect_rule_stats()
            
            assert result["total_rules"] == 50
            assert result["recent_rules"] == 3
            assert "approved" in result["status_breakdown"]
            assert "proposed" in result["status_breakdown"]
            assert "draft" in result["status_breakdown"]

    @pytest.mark.asyncio
    async def test_collect_rule_stats_empty(self):
        """Test rule statistics with empty database."""
        with patch('scripts.progress_report_worker.SessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_query = MagicMock()
            mock_session_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 0
            mock_query.all.return_value = []
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            result = await collect_rule_stats()
            
            assert result["total_rules"] == 0
            assert result["recent_rules"] == 0
            assert result["status_breakdown"] == {}


class TestWorkerStatsCollection:
    """Test worker statistics collection."""

    @pytest.mark.asyncio
    async def test_collect_worker_stats_basic(self):
        """Test basic worker statistics collection."""
        with patch('scripts.progress_report_worker.requests.get') as mock_get:
            # Mock worker health responses
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "healthy",
                "uptime": 3600,
                "processed_jobs": 100
            }
            
            result = await collect_worker_stats()
            
            assert "memory_enrichment" in result
            assert "memory_similarity" in result
            assert "progress_report" in result
            assert result["memory_enrichment"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_collect_worker_stats_unhealthy(self):
        """Test worker statistics with unhealthy workers."""
        with patch('scripts.progress_report_worker.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            result = await collect_worker_stats()
            
            assert "memory_enrichment" in result
            assert result["memory_enrichment"]["status"] == "unhealthy"
            assert "error" in result["memory_enrichment"]


class TestSystemStatsCollection:
    """Test system statistics collection."""

    @pytest.mark.asyncio
    async def test_collect_system_stats_basic(self):
        """Test basic system statistics collection."""
        with patch('scripts.progress_report_worker.psutil') as mock_psutil:
            # Mock system metrics
            mock_psutil.cpu_percent.return_value = 25.5
            mock_psutil.virtual_memory.return_value = MagicMock(
                percent=60.0,
                available=1024 * 1024 * 1024  # 1GB
            )
            mock_psutil.disk_usage.return_value = MagicMock(
                percent=45.0,
                free=1024 * 1024 * 1024 * 10  # 10GB
            )
            
            result = await collect_system_stats()
            
            assert result["cpu_usage"] == 25.5
            assert result["memory_usage"] == 60.0
            assert result["disk_usage"] == 45.0
            assert "memory_available_gb" in result
            assert "disk_free_gb" in result

    @pytest.mark.asyncio
    async def test_collect_system_stats_error(self):
        """Test system statistics collection with errors."""
        with patch('scripts.progress_report_worker.psutil') as mock_psutil:
            mock_psutil.cpu_percent.side_effect = Exception("CPU error")
            
            result = await collect_system_stats()
            
            assert result["cpu_usage"] == 0.0
            assert "error" in result


class TestGrowthRateCalculation:
    """Test growth rate calculation functions."""

    def test_calculate_growth_rate_positive(self):
        """Test positive growth rate calculation."""
        old_count = 100
        new_count = 150
        days = 7
        
        rate = calculate_growth_rate(old_count, new_count, days)
        
        assert rate > 0
        assert rate == pytest.approx(50.0, rel=0.1)  # 50% growth

    def test_calculate_growth_rate_negative(self):
        """Test negative growth rate calculation."""
        old_count = 150
        new_count = 100
        days = 7
        
        rate = calculate_growth_rate(old_count, new_count, days)
        
        assert rate < 0
        assert rate == pytest.approx(-33.33, rel=0.1)  # ~33% decline

    def test_calculate_growth_rate_zero(self):
        """Test zero growth rate calculation."""
        old_count = 100
        new_count = 100
        days = 7
        
        rate = calculate_growth_rate(old_count, new_count, days)
        
        assert rate == 0.0

    def test_calculate_growth_rate_zero_days(self):
        """Test growth rate calculation with zero days."""
        old_count = 100
        new_count = 150
        days = 0
        
        rate = calculate_growth_rate(old_count, new_count, days)
        
        assert rate == 0.0


class TestHealthScoreCalculation:
    """Test health score calculation functions."""

    def test_calculate_health_score_all_healthy(self):
        """Test health score calculation with all healthy components."""
        stats = {
            "memory_stats": {"total_memories": 100},
            "rule_stats": {"total_rules": 50},
            "worker_stats": {
                "memory_enrichment": {"status": "healthy"},
                "memory_similarity": {"status": "healthy"},
                "progress_report": {"status": "healthy"}
            },
            "system_stats": {
                "cpu_usage": 25.0,
                "memory_usage": 60.0,
                "disk_usage": 45.0
            }
        }
        
        score = calculate_health_score(stats)
        
        assert score > 80  # High score for healthy system

    def test_calculate_health_score_unhealthy_workers(self):
        """Test health score calculation with unhealthy workers."""
        stats = {
            "memory_stats": {"total_memories": 100},
            "rule_stats": {"total_rules": 50},
            "worker_stats": {
                "memory_enrichment": {"status": "unhealthy"},
                "memory_similarity": {"status": "healthy"},
                "progress_report": {"status": "healthy"}
            },
            "system_stats": {
                "cpu_usage": 25.0,
                "memory_usage": 60.0,
                "disk_usage": 45.0
            }
        }
        
        score = calculate_health_score(stats)
        
        assert score < 80  # Lower score due to unhealthy worker

    def test_calculate_health_score_high_system_usage(self):
        """Test health score calculation with high system usage."""
        stats = {
            "memory_stats": {"total_memories": 100},
            "rule_stats": {"total_rules": 50},
            "worker_stats": {
                "memory_enrichment": {"status": "healthy"},
                "memory_similarity": {"status": "healthy"},
                "progress_report": {"status": "healthy"}
            },
            "system_stats": {
                "cpu_usage": 95.0,  # Very high CPU
                "memory_usage": 90.0,  # Very high memory
                "disk_usage": 85.0  # Very high disk
            }
        }
        
        score = calculate_health_score(stats)
        
        assert score < 60  # Lower score due to high system usage


class TestReportFormatting:
    """Test report formatting functions."""

    def test_format_report_basic(self):
        """Test basic report formatting."""
        stats = {
            "memory_stats": {
                "total_memories": 100,
                "recent_memories": 10,
                "growth_rate": 15.5,
                "top_namespaces": {"docker": 25, "python": 20}
            },
            "rule_stats": {
                "total_rules": 50,
                "recent_rules": 5,
                "status_breakdown": {"approved": 30, "proposed": 15, "draft": 5}
            },
            "worker_stats": {
                "memory_enrichment": {"status": "healthy", "uptime": 3600},
                "memory_similarity": {"status": "healthy", "uptime": 3600},
                "progress_report": {"status": "healthy", "uptime": 3600}
            },
            "system_stats": {
                "cpu_usage": 25.0,
                "memory_usage": 60.0,
                "disk_usage": 45.0
            }
        }
        
        report = format_report(stats)
        
        assert "Memory System" in report
        assert "Rule System" in report
        assert "Worker Status" in report
        assert "System Health" in report
        assert "100" in report  # Total memories
        assert "50" in report   # Total rules

    def test_format_report_empty_stats(self):
        """Test report formatting with empty statistics."""
        stats = {
            "memory_stats": {"total_memories": 0, "recent_memories": 0},
            "rule_stats": {"total_rules": 0, "recent_rules": 0},
            "worker_stats": {},
            "system_stats": {}
        }
        
        report = format_report(stats)
        
        assert "Memory System" in report
        assert "0" in report  # Zero memories
        assert "No data available" in report or "0" in report


class TestProgressReportGeneration:
    """Test the main progress report generation."""

    @pytest.mark.asyncio
    async def test_generate_progress_report_success(self):
        """Test successful progress report generation."""
        with patch('scripts.progress_report_worker.collect_memory_stats') as mock_memory:
            with patch('scripts.progress_report_worker.collect_rule_stats') as mock_rules:
                with patch('scripts.progress_report_worker.collect_worker_stats') as mock_workers:
                    with patch('scripts.progress_report_worker.collect_system_stats') as mock_system:
                        # Mock all stats collection
                        mock_memory.return_value = {"total_memories": 100}
                        mock_rules.return_value = {"total_rules": 50}
                        mock_workers.return_value = {"memory_enrichment": {"status": "healthy"}}
                        mock_system.return_value = {"cpu_usage": 25.0}
                        
                        result = await generate_progress_report()
                        
                        assert result["status"] == "success"
                        assert "memory_stats" in result
                        assert "rule_stats" in result
                        assert "worker_stats" in result
                        assert "system_stats" in result
                        assert "health_score" in result
                        assert "formatted_report" in result

    @pytest.mark.asyncio
    async def test_generate_progress_report_partial_failure(self):
        """Test progress report generation with partial failures."""
        with patch('scripts.progress_report_worker.collect_memory_stats') as mock_memory:
            with patch('scripts.progress_report_worker.collect_rule_stats') as mock_rules:
                with patch('scripts.progress_report_worker.collect_worker_stats') as mock_workers:
                    with patch('scripts.progress_report_worker.collect_system_stats') as mock_system:
                        # Mock some failures
                        mock_memory.return_value = {"total_memories": 100}
                        mock_rules.side_effect = Exception("Database error")
                        mock_workers.return_value = {"memory_enrichment": {"status": "healthy"}}
                        mock_system.return_value = {"cpu_usage": 25.0}
                        
                        result = await generate_progress_report()
                        
                        assert result["status"] == "partial_success"
                        assert "memory_stats" in result
                        assert "rule_stats" not in result
                        assert "error" in result


class TestProgressJob:
    """Test the main progress job processing."""

    @pytest.mark.asyncio
    async def test_process_progress_job_success(self):
        """Test successful progress job processing."""
        job_config = {
            "scope": "all",
            "include_system_stats": True,
            "include_worker_stats": True
        }
        
        with patch('scripts.progress_report_worker.generate_progress_report') as mock_generate:
            mock_generate.return_value = {
                "status": "success",
                "memory_stats": {"total_memories": 100},
                "formatted_report": "Test report"
            }
            
            result = await process_progress_job(job_config)
            
            assert result["status"] == "success"
            assert result["processed"] == 1
            assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_process_progress_job_failure(self):
        """Test progress job processing with failure."""
        job_config = {"scope": "all"}
        
        with patch('scripts.progress_report_worker.generate_progress_report') as mock_generate:
            mock_generate.side_effect = Exception("Report generation failed")
            
            result = await process_progress_job(job_config)
            
            assert result["status"] == "error"
            assert "Report generation failed" in result["error"]

    @pytest.mark.asyncio
    async def test_process_progress_job_minimal_config(self):
        """Test progress job with minimal configuration."""
        job_config = {
            "scope": "all",
            "include_system_stats": False,
            "include_worker_stats": False
        }
        
        with patch('scripts.progress_report_worker.generate_progress_report') as mock_generate:
            mock_generate.return_value = {
                "status": "success",
                "memory_stats": {"total_memories": 100},
                "formatted_report": "Test report"
            }
            
            result = await process_progress_job(job_config)
            
            assert result["status"] == "success"
            assert result["processed"] == 1 
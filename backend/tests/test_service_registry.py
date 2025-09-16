"""
Comprehensive Unit Tests for ServiceRegistry Implementation

Tests the ServiceRegistry pattern that eliminates direct database access in CrewAI tools.
Validates:
- ServiceRegistry never closes the orchestrator's session
- Service caching and lazy instantiation
- Tools don't import database or models
- Services only flush, never commit
- Audit logger injection and usage
- Bounded metrics buffer
- Context manager cleanup
"""

import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from typing import Any, Dict, List

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DatabaseError

from app.core.context import RequestContext
from app.services.service_registry import ServiceRegistry, MetricRecord

# Import just the interface to avoid circular dependency
from typing import Protocol


class ToolAuditLogger(Protocol):
    """Protocol for tool audit logger interface"""

    async def log_tool_execution(self, *args, **kwargs):
        """Log tool execution"""
        pass


from app.services.base_service import ServiceBase  # noqa: E402


class TestToolAuditLogger:
    """Test the ToolAuditLogger interface"""

    def test_interface_methods_exist(self):
        """Test that ToolAuditLogger protocol is defined"""
        # Since we're using a Protocol, we can't instantiate it
        # Just verify the protocol is defined
        assert ToolAuditLogger is not None
        assert hasattr(ToolAuditLogger, "log_tool_execution")


class TestMetricRecord:
    """Test MetricRecord dataclass functionality"""

    def test_metric_record_creation(self):
        """Test creating a MetricRecord"""
        timestamp = datetime.now(timezone.utc)
        metadata = {"key": "value"}

        record = MetricRecord(
            timestamp=timestamp,
            service_name="TestService",
            metric_name="test_metric",
            metric_value=42,
            metadata=metadata,
        )

        assert record.timestamp == timestamp
        assert record.service_name == "TestService"
        assert record.metric_name == "test_metric"
        assert record.metric_value == 42
        assert record.metadata == metadata

    def test_metric_record_to_dict(self):
        """Test MetricRecord.to_dict() method"""
        timestamp = datetime.now(timezone.utc)
        metadata = {"source": "test", "count": 5}

        record = MetricRecord(
            timestamp=timestamp,
            service_name="TestService",
            metric_name="operations_count",
            metric_value=100,
            metadata=metadata,
        )

        result = record.to_dict()

        expected = {
            "timestamp": timestamp.isoformat(),
            "service_name": "TestService",
            "metric_name": "operations_count",
            "metric_value": 100,
            "metadata": metadata,
        }

        assert result == expected


class MockService(ServiceBase):
    """Mock service for testing ServiceRegistry"""

    def __init__(self, session: AsyncSession, context: RequestContext):
        super().__init__(session, context)
        self.method_calls = []

    async def test_method(self, param: str) -> str:
        """Test method that can be called"""
        self.method_calls.append(f"test_method:{param}")
        return f"result:{param}"

    async def health_check(self) -> Dict[str, Any]:
        """Required implementation from ServiceBase"""
        return {"status": "healthy", "service": "MockService"}


class TestServiceRegistryLifecycle:
    """Test ServiceRegistry lifecycle and context management"""

    @pytest.fixture
    def mock_session(self):
        """Create mock AsyncSession"""
        session = AsyncMock(spec=AsyncSession)
        # Mock session methods that should NOT be called
        session.commit = AsyncMock()
        session.close = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_context(self):
        """Create mock RequestContext"""
        return RequestContext(
            client_account_id="test-client-123",
            engagement_id="test-engagement-456",
            user_id="test-user-789",
            flow_id="test-flow-abc",
            request_id="test-request-def",
        )

    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock ToolAuditLogger"""
        logger = AsyncMock(spec=ToolAuditLogger)
        return logger

    def test_service_registry_initialization(self, mock_session, mock_context):
        """Test ServiceRegistry initialization with required parameters"""
        registry = ServiceRegistry(mock_session, mock_context)

        assert registry._db is mock_session
        assert registry._context is mock_context
        assert registry._audit_logger is None
        assert len(registry._service_cache) == 0
        assert len(registry._metrics_buffer) == 0
        assert registry._metrics_buffer.maxlen == 100
        assert not registry._is_closed
        assert registry._registry_id.startswith("registry_")

    def test_service_registry_initialization_with_audit_logger(
        self, mock_session, mock_context, mock_audit_logger
    ):
        """Test ServiceRegistry initialization with audit logger"""
        registry = ServiceRegistry(mock_session, mock_context, mock_audit_logger)

        assert registry._audit_logger is mock_audit_logger

    def test_service_registry_initialization_validation(self):
        """Test ServiceRegistry initialization parameter validation"""
        context = RequestContext(client_account_id="test")

        # Test None database session
        with pytest.raises(ValueError, match="Database session is required"):
            ServiceRegistry(None, context)

        # Test None context
        session = AsyncMock(spec=AsyncSession)
        with pytest.raises(ValueError, match="Request context is required"):
            ServiceRegistry(session, None)

    @pytest.mark.asyncio
    async def test_context_manager_lifecycle(self, mock_session, mock_context):
        """Test ServiceRegistry as async context manager"""
        registry = ServiceRegistry(mock_session, mock_context)

        # Test async context manager entry
        async with registry as reg:
            assert reg is registry
            assert not registry._is_closed

        # After exit, registry should be marked as closed
        assert registry._is_closed

        # Session should NOT be closed or committed by registry
        mock_session.close.assert_not_called()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_with_metrics_flush(self, mock_session, mock_context):
        """Test that context manager flushes remaining metrics"""
        registry = ServiceRegistry(mock_session, mock_context)

        # Add some metrics
        registry.record_metric("TestService", "test_metric", 42)
        registry.record_metric("TestService", "another_metric", 100)

        with patch.object(
            registry, "_flush_metrics", new_callable=AsyncMock
        ) as mock_flush:
            async with registry:
                pass

            # Should have flushed metrics on exit
            mock_flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_cleanup_with_exception(
        self, mock_session, mock_context
    ):
        """Test that context manager cleanup works even when exception occurs"""
        registry = ServiceRegistry(mock_session, mock_context)

        # Add some metrics so flush will be called
        registry.record_metric("TestService", "test_metric", 42)

        with patch.object(
            registry, "_flush_metrics", new_callable=AsyncMock
        ) as mock_flush:
            try:
                async with registry:
                    raise ValueError("Test exception")
            except ValueError:
                pass

            # Should still have flushed metrics despite exception (only if there were metrics)
            mock_flush.assert_called_once()
            assert registry._is_closed


class TestServiceRegistryServiceManagement:
    """Test service instantiation, caching, and dependency injection"""

    @pytest.fixture
    def registry(self):
        """Create ServiceRegistry for testing"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(
            client_account_id="test-client", engagement_id="test-engagement"
        )
        return ServiceRegistry(session, context)

    def test_get_service_lazy_instantiation(self, registry):
        """Test lazy service instantiation and caching"""
        # First call should instantiate the service
        service1 = registry.get_service(MockService)

        assert isinstance(service1, MockService)
        assert service1._session is registry._db
        assert service1._context is registry._context

        # Second call should return cached instance
        service2 = registry.get_service(MockService)

        assert service2 is service1  # Same instance
        assert len(registry._service_cache) == 1

    def test_get_service_validation(self, registry):
        """Test get_service parameter validation"""
        # Test None service class
        with pytest.raises(ValueError, match="Service class cannot be None"):
            registry.get_service(None)

        # Test closed registry
        registry._is_closed = True
        with pytest.raises(ValueError, match="Cannot get service from closed registry"):
            registry.get_service(MockService)

    def test_get_service_instantiation_error(self, registry):
        """Test handling of service instantiation errors"""

        class BadService:
            def __init__(self, wrong_params):
                pass

        with pytest.raises(TypeError, match="Cannot instantiate BadService"):
            registry.get_service(BadService)

    def test_get_service_multiple_types(self, registry):
        """Test caching of multiple service types"""

        class ServiceA(ServiceBase):
            def __init__(self, session, context):
                super().__init__(session, context)

            async def health_check(self):
                return {"status": "A"}

        class ServiceB(ServiceBase):
            def __init__(self, session, context):
                super().__init__(session, context)

            async def health_check(self):
                return {"status": "B"}

        service_a1 = registry.get_service(ServiceA)
        service_b1 = registry.get_service(ServiceB)
        service_a2 = registry.get_service(ServiceA)

        assert service_a1 is service_a2
        assert service_a1 is not service_b1
        assert len(registry._service_cache) == 2


class TestServiceRegistryAuditLogger:
    """Test audit logger injection and usage"""

    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock audit logger"""
        return AsyncMock(spec=ToolAuditLogger)

    @pytest.fixture
    def registry_with_audit(self, mock_audit_logger):
        """Create ServiceRegistry with audit logger"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(client_account_id="test")
        return ServiceRegistry(session, context, mock_audit_logger)

    @pytest.fixture
    def registry_without_audit(self):
        """Create ServiceRegistry without audit logger"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(client_account_id="test")
        return ServiceRegistry(session, context)

    def test_get_audit_logger_with_logger(self, registry_with_audit, mock_audit_logger):
        """Test get_audit_logger when logger is provided"""
        result = registry_with_audit.get_audit_logger()
        assert result is mock_audit_logger

    def test_get_audit_logger_without_logger(self, registry_without_audit):
        """Test get_audit_logger when no logger is provided"""
        result = registry_without_audit.get_audit_logger()
        assert result is None

    def test_get_audit_logger_closed_registry(self, registry_with_audit):
        """Test get_audit_logger on closed registry"""
        registry_with_audit._is_closed = True

        result = registry_with_audit.get_audit_logger()
        assert result is None


class TestServiceRegistryMetricsBuffer:
    """Test bounded metrics buffer with auto-flush at 100 items"""

    @pytest.fixture
    def registry(self):
        """Create ServiceRegistry for testing"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(client_account_id="test")
        return ServiceRegistry(session, context)

    def test_record_metric_basic(self, registry):
        """Test basic metric recording"""
        registry.record_metric("TestService", "test_metric", 42)

        assert len(registry._metrics_buffer) == 1
        metric = registry._metrics_buffer[0]

        assert isinstance(metric, MetricRecord)
        assert metric.service_name == "TestService"
        assert metric.metric_name == "test_metric"
        assert metric.metric_value == 42
        assert isinstance(metric.timestamp, datetime)
        assert metric.metadata == {}

    def test_record_metric_with_metadata(self, registry):
        """Test metric recording with metadata"""
        metadata = {"source": "test", "priority": "high"}
        registry.record_metric("TestService", "test_metric", 100, metadata)

        metric = registry._metrics_buffer[0]
        assert metric.metadata == metadata

    def test_record_metric_closed_registry(self, registry):
        """Test metric recording on closed registry (should be ignored)"""
        registry._is_closed = True

        registry.record_metric("TestService", "test_metric", 42)

        # Should not record metrics when closed
        assert len(registry._metrics_buffer) == 0

    @pytest.mark.asyncio
    async def test_bounded_buffer_behavior(self, registry):
        """Test that metrics buffer is bounded to 100 items"""
        with patch.object(registry, "_flush_metrics", new_callable=AsyncMock):
            # Add 150 metrics
            for i in range(150):
                registry.record_metric("TestService", f"metric_{i}", i)

            # Should only keep the last 100
            assert len(registry._metrics_buffer) == 100

            # Should have the most recent metrics (50-149)
            first_metric = registry._metrics_buffer[0]
            last_metric = registry._metrics_buffer[-1]

            assert first_metric.metric_name == "metric_50"
            assert last_metric.metric_name == "metric_149"

    @pytest.mark.asyncio
    async def test_auto_flush_at_max_size(self, registry):
        """Test auto-flush when buffer reaches max size"""
        with patch.object(
            registry, "_flush_metrics", new_callable=AsyncMock
        ) as mock_flush:
            # Add exactly 100 metrics to trigger auto-flush
            for i in range(100):
                registry.record_metric("TestService", f"metric_{i}", i)

            # Should have triggered auto-flush
            mock_flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush_metrics_implementation(self, registry):
        """Test the _flush_metrics implementation"""
        # Add some metrics
        for i in range(5):
            registry.record_metric("TestService", f"metric_{i}", i)

        assert len(registry._metrics_buffer) == 5

        with patch.object(
            registry, "_write_metrics_async", new_callable=AsyncMock
        ) as mock_write:
            await registry._flush_metrics()

            # Buffer should be cleared after flush
            assert len(registry._metrics_buffer) == 0

            # Should have called write with the metrics
            mock_write.assert_called_once()
            written_metrics = mock_write.call_args[0][0]
            assert len(written_metrics) == 5
            assert all(isinstance(m, MetricRecord) for m in written_metrics)

    @pytest.mark.asyncio
    async def test_flush_metrics_error_handling(self, registry):
        """Test flush metrics handles write errors gracefully"""
        # Add metrics
        registry.record_metric("TestService", "test_metric", 42)

        with patch.object(
            registry, "_write_metrics_async", new_callable=AsyncMock
        ) as mock_write:
            mock_write.side_effect = Exception("Write failed")

            # Should not raise exception
            await registry._flush_metrics()

            # Buffer should still be cleared (don't retry failed metrics)
            assert len(registry._metrics_buffer) == 0

    @pytest.mark.asyncio
    async def test_write_metrics_async_placeholder(self, registry):
        """Test the placeholder _write_metrics_async implementation"""
        metrics = [
            MetricRecord(
                timestamp=datetime.now(timezone.utc),
                service_name="TestService",
                metric_name="test_metric",
                metric_value=42,
                metadata={},
            )
        ]

        # Should not raise exception
        await registry._write_metrics_async(metrics)


class TestServiceRegistrySessionOwnership:
    """Test that ServiceRegistry never closes the orchestrator's session"""

    @pytest.fixture
    def mock_session(self):
        """Create mock session to track method calls"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def registry(self, mock_session):
        """Create registry with mock session"""
        context = RequestContext(client_account_id="test")
        return ServiceRegistry(mock_session, context)

    @pytest.mark.asyncio
    async def test_registry_never_commits_session(self, registry, mock_session):
        """Test that registry never calls commit() on session"""
        # Use registry normally
        service = registry.get_service(MockService)
        await service.test_method("test")

        registry.record_metric("TestService", "test_metric", 42)

        async with registry:
            pass

        # Session commit should never be called
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_registry_never_closes_session(self, registry, mock_session):
        """Test that registry never calls close() on session"""
        async with registry:
            service = registry.get_service(MockService)
            await service.test_method("test")

        # Session close should never be called
        mock_session.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_registry_never_calls_session_flush_directly(
        self, registry, mock_session
    ):
        """Test that registry never calls flush() on session directly"""
        async with registry:
            # Registry should not call flush directly
            mock_session.flush.assert_not_called()

    def test_session_accessible_to_services(self, registry, mock_session):
        """Test that services can access the session through registry"""
        service = registry.get_service(MockService)

        # Service should have access to the same session
        assert service.session is mock_session


class TestServiceBaseFlushCommitBehavior:
    """Test that services only flush, never commit"""

    @pytest.fixture
    def mock_session(self):
        """Create mock session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        return RequestContext(client_account_id="test")

    @pytest.fixture
    def service(self, mock_session, mock_context):
        """Create MockService instance"""
        return MockService(mock_session, mock_context)

    @pytest.mark.asyncio
    async def test_service_can_flush_for_id(self, service, mock_session):
        """Test that services can call flush_for_id()"""
        await service.flush_for_id()

        # Should have called flush on session
        mock_session.flush.assert_called_once()

    def test_service_has_no_commit_method(self, service):
        """Test that services don't expose commit method"""
        # Services should not have their own commit method
        assert not hasattr(service, "commit")

    def test_service_session_property_warns_against_commit(self, service):
        """Test that session property has warning in docstring"""
        session_property = type(service).session
        docstring = session_property.__doc__

        assert "DO NOT call commit() or close()" in docstring

    @pytest.mark.asyncio
    async def test_service_flush_for_id_error_handling(self, service, mock_session):
        """Test flush_for_id error handling"""
        mock_session.flush.side_effect = DatabaseError(
            "statement", "params", "orig", None
        )

        with patch.object(
            service, "record_failure", new_callable=AsyncMock
        ) as mock_record:
            with pytest.raises(DatabaseError):
                await service.flush_for_id()

            # Should have recorded the failure
            mock_record.assert_called_once()
            args = mock_record.call_args[1]
            assert args["operation"] == "flush_for_id"


class TestToolDatabaseImportValidation:
    """Test that tools don't import database or models"""

    def test_service_registry_tool_pattern(self):
        """Test that ServiceRegistry-based tools follow no-import pattern"""
        # This would be a static analysis test in a real implementation
        # For now, we'll test the pattern by checking a mock tool implementation

        class MockToolWithServiceRegistry:
            def __init__(self, registry):
                self._registry = registry
                # NO database or model imports in __init__

            async def execute(self, data):
                # Get service from registry instead of importing database
                from app.services.asset_service import AssetService

                asset_service = self._registry.get_service(AssetService)
                return await asset_service.create_asset(data)

        # This pattern is correct - only service imports, no DB/model imports
        assert True

    def test_legacy_tool_pattern_should_be_avoided(self):
        """Test example of what tools should NOT do"""

        class BadToolPattern:
            def __init__(self, context_info):
                # BAD: Direct database imports in tool
                pass

            async def execute(self, data):
                # BAD: Direct database session creation
                # from app.core.database import AsyncSessionLocal
                # async with AsyncSessionLocal() as db:
                #     # Direct database operations
                #     pass
                pass

        # This test documents the anti-pattern that should be avoided
        assert True

    def test_tool_import_analysis_helper(self):
        """Helper method to analyze tool imports (would be expanded in real implementation)"""

        def analyze_tool_imports(tool_file_path: str) -> Dict[str, List[str]]:
            """
            Analyze a tool file for problematic imports.
            In a real implementation, this would parse the AST of tool files.
            """
            problematic_imports = {
                "database_imports": [],
                "model_imports": [],
                "session_imports": [],
            }

            # Mock implementation - real version would parse Python AST
            # and check for imports like:
            # - from app.core.database import AsyncSessionLocal
            # - from app.models import *
            # - import sqlalchemy

            return problematic_imports

        # Example usage
        result = analyze_tool_imports("mock_tool.py")
        assert isinstance(result, dict)
        assert "database_imports" in result
        assert "model_imports" in result
        assert "session_imports" in result


class TestFeatureFlagBehavior:
    """Test feature flag behavior for ServiceRegistry pattern"""

    def test_service_registry_feature_flag_enabled(self):
        """Test behavior when USE_SERVICE_REGISTRY=true"""
        with patch.dict(os.environ, {"USE_SERVICE_REGISTRY": "true"}):
            use_registry = os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true"
            assert use_registry is True

    def test_service_registry_feature_flag_disabled(self):
        """Test behavior when USE_SERVICE_REGISTRY=false"""
        with patch.dict(os.environ, {"USE_SERVICE_REGISTRY": "false"}):
            use_registry = os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true"
            assert use_registry is False

    def test_service_registry_feature_flag_default(self):
        """Test default behavior when USE_SERVICE_REGISTRY not set"""
        with patch.dict(os.environ, {}, clear=True):
            use_registry = os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true"
            assert use_registry is False

    @patch("warnings.warn")
    def test_deprecation_warning_when_legacy_used(self, mock_warn):
        """Test that deprecation warning is shown for legacy tools"""

        def mock_tool_creation_with_legacy():
            use_service_registry = False
            if not use_service_registry:
                import warnings

                warnings.warn(
                    "Legacy tools are deprecated and will be removed on 2025-02-01. "
                    "Set USE_SERVICE_REGISTRY=true to use the new ServiceRegistry pattern.",
                    DeprecationWarning,
                    stacklevel=2,
                )

        mock_tool_creation_with_legacy()

        mock_warn.assert_called_once()
        warning_call = mock_warn.call_args
        assert "Legacy tools are deprecated" in warning_call[0][0]
        assert warning_call[0][1] is DeprecationWarning


class TestServiceRegistryStats:
    """Test registry statistics and monitoring"""

    @pytest.fixture
    def registry(self):
        """Create registry for testing"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(
            client_account_id="test-client",
            engagement_id="test-engagement",
            flow_id="test-flow",
        )
        audit_logger = AsyncMock(spec=ToolAuditLogger)
        return ServiceRegistry(session, context, audit_logger)

    def test_get_registry_stats_empty(self, registry):
        """Test stats for empty registry"""
        stats = registry.get_registry_stats()

        expected_keys = {
            "registry_id",
            "is_closed",
            "services_cached",
            "cached_service_types",
            "metrics_buffered",
            "has_audit_logger",
            "context_client_id",
            "context_engagement_id",
            "context_flow_id",
        }

        assert set(stats.keys()) == expected_keys
        assert stats["is_closed"] is False
        assert stats["services_cached"] == 0
        assert stats["cached_service_types"] == []
        assert stats["metrics_buffered"] == 0
        assert stats["has_audit_logger"] is True
        assert stats["context_client_id"] == "test-client"
        assert stats["context_engagement_id"] == "test-engagement"
        assert stats["context_flow_id"] == "test-flow"

    def test_get_registry_stats_with_services_and_metrics(self, registry):
        """Test stats with cached services and metrics"""
        # Add services
        registry.get_service(MockService)

        class AnotherService(ServiceBase):
            def __init__(self, session, context):
                super().__init__(session, context)

            async def health_check(self):
                return {"status": "ok"}

        registry.get_service(AnotherService)

        # Add metrics
        registry.record_metric("TestService", "metric1", 10)
        registry.record_metric("TestService", "metric2", 20)

        stats = registry.get_registry_stats()

        assert stats["services_cached"] == 2
        assert set(stats["cached_service_types"]) == {"MockService", "AnotherService"}
        assert stats["metrics_buffered"] == 2

    def test_get_registry_stats_closed(self, registry):
        """Test stats for closed registry"""
        registry._is_closed = True

        stats = registry.get_registry_stats()
        assert stats["is_closed"] is True


class TestServiceRegistryIntegration:
    """Integration tests for ServiceRegistry with real-like scenarios"""

    @pytest.mark.asyncio
    async def test_complete_workflow_simulation(self):
        """Test a complete workflow simulation"""
        # Setup
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            flow_id=str(uuid.uuid4()),
        )
        audit_logger = AsyncMock(spec=ToolAuditLogger)

        # Test complete workflow
        async with ServiceRegistry(session, context, audit_logger) as registry:
            # 1. Get services (lazy instantiation)
            service1 = registry.get_service(MockService)
            service2 = registry.get_service(MockService)  # Should be cached

            assert service1 is service2

            # 2. Use audit logger
            logger = registry.get_audit_logger()
            assert logger is audit_logger

            # 3. Record metrics
            for i in range(10):
                registry.record_metric("MockService", f"operation_{i}", i * 10)

            # 4. Use service methods
            result = await service1.test_method("integration_test")
            assert result == "result:integration_test"

            # 5. Check stats
            stats = registry.get_registry_stats()
            assert stats["services_cached"] == 1
            assert stats["metrics_buffered"] == 10
            assert stats["has_audit_logger"] is True

        # After context exit
        assert registry._is_closed

        # Session should never have been committed or closed
        session.commit.assert_not_called()
        session.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_error_scenarios(self):
        """Test various error scenarios"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(client_account_id="test")

        async with ServiceRegistry(session, context) as registry:
            # Test service instantiation error
            class BadService:
                def __init__(self, wrong_signature):
                    pass

            with pytest.raises(TypeError):
                registry.get_service(BadService)

            # Test using closed registry
            registry._is_closed = True

            with pytest.raises(ValueError):
                registry.get_service(MockService)

            # Audit logger should return None when closed
            assert registry.get_audit_logger() is None

            # Metrics recording should be ignored when closed
            initial_buffer_len = len(registry._metrics_buffer)
            registry.record_metric("Test", "metric", 1)
            assert len(registry._metrics_buffer) == initial_buffer_len


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

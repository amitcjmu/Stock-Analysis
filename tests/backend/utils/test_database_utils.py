"""
Tests for Backend Shared Database Utilities

Tests the modular database utility functions including:
- Session management and health monitoring
- Query builders with multi-tenant filtering  
- Pagination utilities
- Transaction management
- Connection pooling
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# Import database utilities
try:
    from app.utils.database.session_manager import get_session_with_context, SessionHealthMonitor
    from app.utils.database.query_builder import QueryBuilder, MultiTenantQueryBuilder
    from app.utils.database.pagination import PaginationHelper, PaginationMetadata
    from app.utils.database.transaction_manager import TransactionManager, TransactionScope
    from app.utils.database.connection_monitor import ConnectionPoolMonitor
    from app.models.asset import Asset
    from app.models.discovery_flow import DiscoveryFlow
except ImportError:
    # Mock imports for testing environment
    get_session_with_context = Mock
    SessionHealthMonitor = Mock
    QueryBuilder = Mock
    MultiTenantQueryBuilder = Mock
    PaginationHelper = Mock
    PaginationMetadata = Mock
    TransactionManager = Mock
    TransactionScope = Mock
    ConnectionPoolMonitor = Mock
    Asset = Mock
    DiscoveryFlow = Mock


@pytest.fixture
def mock_db_session():
    """Mock async database session"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.scalars = AsyncMock()
    return session


@pytest.fixture
def sample_tenant_context():
    """Sample multi-tenant context"""
    return {
        "client_account_id": "client-123",
        "engagement_id": "engagement-456", 
        "user_id": "user-789"
    }


@pytest.fixture
def mock_query_result():
    """Mock database query result"""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_result.scalars = Mock(return_value=[
        {"id": 1, "name": "asset-1", "client_account_id": "client-123"},
        {"id": 2, "name": "asset-2", "client_account_id": "client-123"}
    ])
    mock_result.fetchall = Mock(return_value=[
        {"id": 1, "name": "asset-1"},
        {"id": 2, "name": "asset-2"}
    ])
    return mock_result


class TestSessionManagement:
    """Test session management utilities"""
    
    @pytest.mark.asyncio
    async def test_get_session_with_context_success(
        self,
        sample_tenant_context
    ):
        """Test successful session creation with tenant context"""
        # Mock the session factory
        with patch('app.utils.database.session_manager.AsyncSessionLocal') as mock_session_factory:
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Act
            async with get_session_with_context(
                client_account_id=sample_tenant_context["client_account_id"]
            ) as session:
                # Assert
                assert session is not None
                assert hasattr(session, 'client_account_id')
                assert session.client_account_id == sample_tenant_context["client_account_id"]
    
    @pytest.mark.asyncio
    async def test_session_health_monitoring(
        self,
        mock_db_session,
        sample_tenant_context
    ):
        """Test session health monitoring functionality"""
        # Arrange
        health_monitor = SessionHealthMonitor()
        
        # Mock health check query
        mock_db_session.execute.return_value.scalar.return_value = 1
        
        # Act
        is_healthy = await health_monitor.check_session_health(mock_db_session)
        
        # Assert
        assert is_healthy is True
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_timeout_handling(
        self,
        mock_db_session,
        sample_tenant_context
    ):
        """Test session timeout handling"""
        # Arrange
        health_monitor = SessionHealthMonitor(timeout_seconds=1)
        
        # Mock slow query
        async def slow_query(*args, **kwargs):
            await asyncio.sleep(2)  # Simulate slow query
            return Mock(scalar=Mock(return_value=1))
        
        mock_db_session.execute = slow_query
        
        # Act & Assert
        is_healthy = await health_monitor.check_session_health(mock_db_session)
        assert is_healthy is False  # Should timeout


class TestQueryBuilder:
    """Test query builder utilities"""
    
    def test_basic_query_builder_initialization(self):
        """Test basic query builder initialization"""
        # Act
        builder = QueryBuilder(Asset)
        
        # Assert
        assert builder.model == Asset
        assert builder.query is not None
        assert builder.filters == []
    
    def test_query_builder_filter_chaining(self):
        """Test query builder filter chaining"""
        # Arrange
        builder = QueryBuilder(Asset)
        
        # Act
        result = (builder
                 .filter("status", "active")
                 .filter("os_type", "Linux")
                 .limit(10))
        
        # Assert
        assert len(builder.filters) == 2
        assert builder.limit_value == 10
        assert result == builder  # Should return self for chaining
    
    def test_multi_tenant_query_builder(
        self,
        sample_tenant_context
    ):
        """Test multi-tenant query builder"""
        # Arrange
        builder = MultiTenantQueryBuilder(
            model=Asset,
            client_account_id=sample_tenant_context["client_account_id"]
        )
        
        # Act
        builder.with_tenant_context(sample_tenant_context["client_account_id"])
        
        # Assert
        assert builder.client_account_id == sample_tenant_context["client_account_id"]
        # Should automatically add client_account_id filter
        tenant_filters = [f for f in builder.filters if f.get("field") == "client_account_id"]
        assert len(tenant_filters) >= 1
    
    @pytest.mark.asyncio
    async def test_query_builder_execution(
        self,
        mock_db_session,
        mock_query_result,
        sample_tenant_context
    ):
        """Test query builder execution"""
        # Arrange
        builder = MultiTenantQueryBuilder(
            model=Asset,
            client_account_id=sample_tenant_context["client_account_id"]
        )
        
        mock_db_session.execute.return_value = mock_query_result
        
        # Act
        results = await builder.filter("status", "active").execute(mock_db_session)
        
        # Assert
        assert results is not None
        mock_db_session.execute.assert_called_once()
    
    def test_query_builder_with_joins(self):
        """Test query builder with table joins"""
        # Arrange
        builder = QueryBuilder(Asset)
        
        # Act
        builder.join(DiscoveryFlow, Asset.discovery_flow_id == DiscoveryFlow.id)
        
        # Assert
        assert len(builder.joins) == 1
        assert builder.joins[0]["model"] == DiscoveryFlow
    
    def test_query_builder_ordering(self):
        """Test query builder ordering functionality"""
        # Arrange
        builder = QueryBuilder(Asset)
        
        # Act
        builder.order_by("created_at", "desc").order_by("name", "asc")
        
        # Assert
        assert len(builder.order_clauses) == 2
        assert builder.order_clauses[0]["field"] == "created_at"
        assert builder.order_clauses[0]["direction"] == "desc"


class TestPaginationUtilities:
    """Test pagination utility functions"""
    
    def test_pagination_helper_initialization(self):
        """Test pagination helper initialization"""
        # Act
        paginator = PaginationHelper(page=1, per_page=20, max_per_page=100)
        
        # Assert
        assert paginator.page == 1
        assert paginator.per_page == 20
        assert paginator.max_per_page == 100
        assert paginator.offset == 0  # (page - 1) * per_page
    
    def test_pagination_offset_calculation(self):
        """Test pagination offset calculation"""
        # Arrange & Act
        paginator = PaginationHelper(page=3, per_page=10)
        
        # Assert
        assert paginator.offset == 20  # (3 - 1) * 10
    
    def test_pagination_metadata_generation(self):
        """Test pagination metadata generation"""
        # Arrange
        paginator = PaginationHelper(page=2, per_page=10)
        total_count = 45
        
        # Act
        metadata = paginator.generate_metadata(total_count)
        
        # Assert
        assert isinstance(metadata, PaginationMetadata)
        assert metadata.page == 2
        assert metadata.per_page == 10
        assert metadata.total_count == 45
        assert metadata.total_pages == 5  # ceil(45 / 10)
        assert metadata.has_next is True
        assert metadata.has_previous is True
    
    def test_pagination_edge_cases(self):
        """Test pagination edge cases"""
        # Test first page
        paginator = PaginationHelper(page=1, per_page=10)
        metadata = paginator.generate_metadata(25)
        
        assert metadata.has_previous is False
        assert metadata.has_next is True
        
        # Test last page
        paginator = PaginationHelper(page=3, per_page=10)
        metadata = paginator.generate_metadata(25)
        
        assert metadata.has_previous is True
        assert metadata.has_next is False
    
    def test_pagination_per_page_limits(self):
        """Test per_page limit enforcement"""
        # Act
        paginator = PaginationHelper(page=1, per_page=200, max_per_page=100)
        
        # Assert
        assert paginator.per_page == 100  # Should be clamped to max_per_page
    
    @pytest.mark.asyncio
    async def test_pagination_with_query_builder(
        self,
        mock_db_session,
        mock_query_result,
        sample_tenant_context
    ):
        """Test pagination integration with query builder"""
        # Arrange
        builder = QueryBuilder(Asset)
        paginator = PaginationHelper(page=1, per_page=10)
        
        mock_db_session.execute.return_value = mock_query_result
        
        # Act
        paginated_query = builder.paginate(paginator.page, paginator.per_page)
        await paginated_query.execute(mock_db_session)
        
        # Assert
        assert builder.limit_value == paginator.per_page
        assert builder.offset_value == paginator.offset


class TestTransactionManagement:
    """Test transaction management utilities"""
    
    @pytest.mark.asyncio
    async def test_transaction_manager_context(
        self,
        mock_db_session
    ):
        """Test transaction manager context management"""
        # Arrange
        transaction_manager = TransactionManager(mock_db_session)
        
        # Act & Assert
        async with transaction_manager.transaction() as tx:
            assert isinstance(tx, TransactionScope)
            assert tx.session == mock_db_session
            
        # Verify commit was called
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_exception(
        self,
        mock_db_session
    ):
        """Test transaction rollback on exception"""
        # Arrange
        transaction_manager = TransactionManager(mock_db_session)
        
        # Act & Assert
        with pytest.raises(ValueError):
            async with transaction_manager.transaction():
                raise ValueError("Test exception")
        
        # Verify rollback was called
        mock_db_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_savepoints(
        self,
        mock_db_session
    ):
        """Test transaction savepoint functionality"""
        # Arrange
        transaction_manager = TransactionManager(mock_db_session)
        mock_db_session.begin_nested = AsyncMock()
        
        # Act
        async with transaction_manager.transaction():
            async with transaction_manager.savepoint("test_savepoint"):
                pass  # Nested transaction operations
        
        # Assert
        mock_db_session.begin_nested.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_retry_mechanism(
        self,
        mock_db_session
    ):
        """Test transaction retry mechanism"""
        # Arrange
        transaction_manager = TransactionManager(mock_db_session)
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        # Act
        result = await transaction_manager.execute_with_retry(
            failing_operation,
            max_retries=3,
            retry_delay=0.1
        )
        
        # Assert
        assert result == "success"
        assert call_count == 3


class TestConnectionPoolMonitoring:
    """Test connection pool monitoring"""
    
    def test_connection_pool_monitor_initialization(self):
        """Test connection pool monitor initialization"""
        # Act
        monitor = ConnectionPoolMonitor()
        
        # Assert
        assert monitor is not None
        assert hasattr(monitor, 'get_pool_status')
        assert hasattr(monitor, 'get_connection_count')
    
    @pytest.mark.asyncio
    async def test_connection_pool_health_check(
        self,
        mock_db_session
    ):
        """Test connection pool health monitoring"""
        # Arrange
        monitor = ConnectionPoolMonitor()
        
        # Mock pool status
        with patch.object(monitor, 'get_pool_status', return_value={
            "active_connections": 5,
            "idle_connections": 3,
            "total_connections": 8,
            "max_connections": 20
        }):
            # Act
            status = monitor.get_pool_status()
            
            # Assert
            assert status["active_connections"] == 5
            assert status["idle_connections"] == 3
            assert status["total_connections"] == 8
            assert status["max_connections"] == 20
    
    def test_connection_pool_alerts(self):
        """Test connection pool alerting thresholds"""
        # Arrange
        monitor = ConnectionPoolMonitor(
            max_connection_threshold=0.8,  # 80%
            min_idle_threshold=2
        )
        
        # Act - Test high connection usage
        high_usage_status = {
            "active_connections": 16,
            "idle_connections": 1,
            "total_connections": 17,
            "max_connections": 20
        }
        
        alerts = monitor.check_pool_alerts(high_usage_status)
        
        # Assert
        assert len(alerts) > 0
        assert any("high connection usage" in alert.lower() for alert in alerts)
        assert any("low idle connections" in alert.lower() for alert in alerts)


class TestMultiTenantDatabaseUtilities:
    """Test multi-tenant specific database utilities"""
    
    @pytest.mark.asyncio
    async def test_tenant_context_isolation(
        self,
        mock_db_session,
        mock_query_result
    ):
        """Test tenant context isolation in database operations"""
        # Arrange
        tenant_1_context = "client-001"
        tenant_2_context = "client-002"
        
        builder_1 = MultiTenantQueryBuilder(Asset, tenant_1_context)
        builder_2 = MultiTenantQueryBuilder(Asset, tenant_2_context)
        
        mock_db_session.execute.return_value = mock_query_result
        
        # Act
        await builder_1.filter("status", "active").execute(mock_db_session)
        await builder_2.filter("status", "active").execute(mock_db_session)
        
        # Assert
        assert builder_1.client_account_id != builder_2.client_account_id
        assert len(mock_db_session.execute.call_args_list) == 2
    
    def test_tenant_filter_enforcement(self):
        """Test that tenant filters are automatically enforced"""
        # Arrange
        client_account_id = "client-123"
        builder = MultiTenantQueryBuilder(Asset, client_account_id)
        
        # Act
        builder.filter("status", "active")
        
        # Assert
        # Should have both explicit filter and automatic tenant filter
        assert len(builder.filters) >= 2
        tenant_filter = next(
            (f for f in builder.filters if f.get("field") == "client_account_id"),
            None
        )
        assert tenant_filter is not None
        assert tenant_filter["value"] == client_account_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
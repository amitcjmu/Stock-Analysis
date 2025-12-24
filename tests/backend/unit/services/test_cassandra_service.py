"""
Unit tests for Cassandra Service
Tests all functionality of the Cassandra service for stock search data storage.
"""

import asyncio
import json
from datetime import datetime, timedelta, date
from unittest.mock import AsyncMock, MagicMock, Mock, patch, PropertyMock
from uuid import UUID, uuid4

import pytest

from app.services.cassandra_service import CassandraService, CASSANDRA_AVAILABLE


# Test Fixtures
@pytest.fixture
def mock_cassandra_driver():
    """Mock Cassandra driver components"""
    mock_cluster = MagicMock()
    mock_session = MagicMock()
    mock_cluster.connect.return_value = mock_session

    mock_execution_profile = MagicMock()
    mock_policy = MagicMock()

    with patch('app.services.cassandra_service.Cluster', return_value=mock_cluster), \
         patch('app.services.cassandra_service.ExecutionProfile', return_value=mock_execution_profile), \
         patch('app.services.cassandra_service.TokenAwarePolicy', return_value=mock_policy), \
         patch('app.services.cassandra_service.DCAwareRoundRobinPolicy', return_value=mock_policy), \
         patch('app.services.cassandra_service.SimpleStatement'), \
         patch('app.services.cassandra_service.ConsistencyLevel'):
        yield {
            'cluster': mock_cluster,
            'session': mock_session,
            'execution_profile': mock_execution_profile,
        }


@pytest.fixture
def sample_client_account_id():
    """Sample client account ID"""
    return uuid4()


@pytest.fixture
def sample_engagement_id():
    """Sample engagement ID"""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user ID"""
    return "test_user_123"


@pytest.fixture
def sample_search_data():
    """Sample search data"""
    return {
        'search_query': 'AAPL',
        'search_type': 'symbol',
        'results_count': 10,
        'execution_time_ms': 150,
        'source': 'api',
        'results': [
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'price': 150.0}
        ]
    }


@pytest.fixture
def cassandra_service(mock_cassandra_driver):
    """Create CassandraService instance with mocked driver"""
    with patch('app.services.cassandra_service.CASSANDRA_AVAILABLE', True):
        service = CassandraService()
        service.cluster = mock_cassandra_driver['cluster']
        service.session = mock_cassandra_driver['session']
        service.keyspace = "test_keyspace"
        service.contact_points = ["localhost"]
        service.port = 9042
        return service


@pytest.fixture
def cassandra_service_no_driver():
    """Create CassandraService instance without driver (mock mode)"""
    with patch('app.services.cassandra_service.CASSANDRA_AVAILABLE', False):
        service = CassandraService()
        return service


# Test Classes
class TestCassandraServiceInitialization:
    """Test Cassandra service initialization"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_initialize_success(self, cassandra_service, mock_cassandra_driver):
        """Test successful initialization"""
        mock_session = mock_cassandra_driver['session']
        mock_session.execute.return_value = None

        result = await cassandra_service.initialize()

        assert result is True
        assert cassandra_service._initialized is True
        assert mock_session.execute.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_initialize_no_driver(self, cassandra_service_no_driver):
        """Test initialization when driver is not available"""
        result = await cassandra_service_no_driver.initialize()

        assert result is False
        assert cassandra_service_no_driver._initialized is False


class TestLogStockSearch:
    """Test logging stock searches"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_log_stock_search_success(
        self, cassandra_service, sample_client_account_id,
        sample_engagement_id, sample_user_id, sample_search_data
    ):
        """Test successful search logging"""
        cassandra_service._initialized = True
        mock_session = cassandra_service.session
        mock_session.execute.return_value = None

        search_id = await cassandra_service.log_stock_search(
            client_account_id=sample_client_account_id,
            engagement_id=sample_engagement_id,
            user_id=sample_user_id,
            search_query=sample_search_data['search_query'],
            search_type=sample_search_data['search_type'],
            results_count=sample_search_data['results_count'],
            execution_time_ms=sample_search_data['execution_time_ms'],
            source=sample_search_data['source'],
            results=sample_search_data['results'],
        )

        assert search_id is not None
        assert isinstance(search_id, UUID)
        assert mock_session.execute.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_log_stock_search_no_driver(
        self, cassandra_service_no_driver, sample_client_account_id,
        sample_engagement_id, sample_user_id, sample_search_data
    ):
        """Test logging when driver is not available"""
        search_id = await cassandra_service_no_driver.log_stock_search(
            client_account_id=sample_client_account_id,
            engagement_id=sample_engagement_id,
            user_id=sample_user_id,
            search_query=sample_search_data['search_query'],
        )

        assert search_id is None


class TestGetSearchHistory:
    """Test retrieving search history"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_search_history_success(
        self, cassandra_service, sample_client_account_id, sample_user_id
    ):
        """Test successful history retrieval"""
        cassandra_service._initialized = True

        # Mock search history results
        mock_row = MagicMock()
        mock_row.search_id = uuid4()
        mock_row.search_query = "AAPL"
        mock_row.search_type = "symbol"
        mock_row.results_count = 10
        mock_row.execution_time_ms = 150
        mock_row.source = "api"
        mock_row.search_timestamp = datetime.utcnow()

        mock_result = MagicMock()
        mock_result.__iter__ = Mock(return_value=iter([mock_row]))

        mock_session = cassandra_service.session
        mock_session.execute.return_value = mock_result

        history = await cassandra_service.get_search_history(
            client_account_id=sample_client_account_id,
            user_id=sample_user_id,
            days=30,
            limit=100,
        )

        assert isinstance(history, list)
        assert len(history) > 0
        assert history[0]['search_query'] == "AAPL"
        assert history[0]['search_type'] == "symbol"
        assert 'timestamp' in history[0]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_search_history_no_driver(
        self, cassandra_service_no_driver, sample_client_account_id, sample_user_id
    ):
        """Test history retrieval when driver is not available"""
        history = await cassandra_service_no_driver.get_search_history(
            client_account_id=sample_client_account_id,
            user_id=sample_user_id,
        )

        assert history == []


class TestGetSearchAnalytics:
    """Test retrieving search analytics"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_search_analytics_success(
        self, cassandra_service, sample_client_account_id, sample_user_id
    ):
        """Test successful analytics retrieval"""
        cassandra_service._initialized = True

        # Mock analytics result
        mock_result = MagicMock()
        mock_result.total_searches = 100
        mock_result.unique_queries = 25
        mock_result.avg_results_count = 8.5
        mock_result.avg_execution_time_ms = 120.5
        mock_result.most_searched_symbols = {"AAPL": 20, "MSFT": 15}
        mock_result.search_sources = {"api": 60, "cache": 30, "database": 10}

        mock_session = cassandra_service.session
        mock_session.execute.return_value.one.return_value = mock_result

        analytics = await cassandra_service.get_search_analytics(
            client_account_id=sample_client_account_id,
            user_id=sample_user_id,
            year_month="2025-01",
        )

        assert analytics is not None
        assert analytics['total_searches'] == 100
        assert analytics['unique_queries'] == 25
        assert analytics['avg_results_count'] == 8.5
        assert 'most_searched_symbols' in analytics
        assert 'search_sources' in analytics

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_search_analytics_no_driver(
        self, cassandra_service_no_driver, sample_client_account_id, sample_user_id
    ):
        """Test analytics retrieval when driver is not available"""
        analytics = await cassandra_service_no_driver.get_search_analytics(
            client_account_id=sample_client_account_id,
            user_id=sample_user_id,
        )

        assert analytics is None


class TestGetCachedResults:
    """Test retrieving cached search results"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_cached_results_success(
        self, cassandra_service, sample_client_account_id, sample_user_id
    ):
        """Test successful cache retrieval"""
        cassandra_service._initialized = True

        # Mock cached result
        mock_result = MagicMock()
        mock_result.results = json.dumps([{"symbol": "AAPL", "name": "Apple Inc."}])
        mock_result.expires_at = datetime.utcnow() + timedelta(hours=1)

        mock_session = cassandra_service.session
        mock_session.execute.return_value.one.return_value = mock_result

        cached = await cassandra_service.get_cached_results(
            client_account_id=sample_client_account_id,
            user_id=sample_user_id,
            search_query="AAPL",
        )

        assert cached is not None
        assert isinstance(cached, list)
        assert cached[0]['symbol'] == "AAPL"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_cached_results_no_driver(
        self, cassandra_service_no_driver, sample_client_account_id, sample_user_id
    ):
        """Test cache retrieval when driver is not available"""
        cached = await cassandra_service_no_driver.get_cached_results(
            client_account_id=sample_client_account_id,
            user_id=sample_user_id,
            search_query="AAPL",
        )

        assert cached is None

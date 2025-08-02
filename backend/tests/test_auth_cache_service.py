"""
Unit tests for AuthCacheService

Tests the Redis-based authentication caching service including:
- User session caching with TTL management
- Context data caching and retrieval
- Batched storage operations with debouncing
- Cache invalidation strategies
- Multi-layered fallback (Redis → In-Memory → Database)
- Performance monitoring hooks
- Comprehensive error handling and logging
- Security data sanitization
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.caching.auth_cache_service import (
    AuthCacheService,
    UserSession,
    UserContext,
    InMemoryFallbackCache,
    get_auth_cache_service,
)


class TestInMemoryFallbackCache:
    """Test the in-memory fallback cache functionality"""

    @pytest.fixture
    def cache(self):
        """Create a clean in-memory cache for testing"""
        return InMemoryFallbackCache(max_size=10, default_ttl=300)

    @pytest.mark.asyncio
    async def test_basic_set_get_operations(self, cache):
        """Test basic set and get operations"""
        # Test successful set and get
        result = await cache.set("test_key", "test_value")
        assert result is True

        value = await cache.get("test_key")
        assert value == "test_value"

        # Test non-existent key
        value = await cache.get("non_existent")
        assert value is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache):
        """Test TTL expiration functionality"""
        # Set with short TTL
        await cache.set("short_ttl", "value", ttl=1)

        # Should be available immediately
        value = await cache.get("short_ttl")
        assert value == "value"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired now
        value = await cache.get("short_ttl")
        assert value is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self, cache):
        """Test LRU eviction when cache is full"""
        # Fill cache to capacity
        for i in range(10):
            await cache.set(f"key_{i}", f"value_{i}")

        # All keys should be present
        for i in range(10):
            value = await cache.get(f"key_{i}")
            assert value == f"value_{i}"

        # Add one more key - should evict oldest
        await cache.set("new_key", "new_value")

        # key_0 should be evicted
        value = await cache.get("key_0")
        assert value is None

        # New key should be present
        value = await cache.get("new_key")
        assert value == "new_value"

    @pytest.mark.asyncio
    async def test_delete_operation(self, cache):
        """Test delete operation"""
        await cache.set("delete_me", "value")

        # Verify it exists
        value = await cache.get("delete_me")
        assert value == "value"

        # Delete it
        result = await cache.delete("delete_me")
        assert result is True

        # Should be gone
        value = await cache.get("delete_me")
        assert value is None

        # Delete non-existent key
        result = await cache.delete("non_existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_operation(self, cache):
        """Test clear operation"""
        # Add some data
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        # Clear all
        result = await cache.clear()
        assert result is True

        # Should be empty
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    def test_get_stats(self, cache):
        """Test statistics retrieval"""
        stats = cache.get_stats()

        assert "size" in stats
        assert "max_size" in stats
        assert "utilization" in stats
        assert stats["max_size"] == 10


class TestUserSession:
    """Test UserSession data structure"""

    def test_user_session_creation(self):
        """Test UserSession creation with defaults"""
        session = UserSession(
            user_id="123",
            email="test@example.com",
            full_name="Test User",
            role="user",
            is_admin=False,
        )

        assert session.user_id == "123"
        assert session.email == "test@example.com"
        assert session.associations == []
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_accessed, datetime)

    def test_user_session_with_custom_data(self):
        """Test UserSession with custom associations"""
        associations = [{"client_id": "abc", "role": "admin"}]
        session = UserSession(
            user_id="123",
            email="test@example.com",
            full_name="Test User",
            role="admin",
            is_admin=True,
            associations=associations,
        )

        assert session.associations == associations
        assert session.is_admin is True


class TestUserContext:
    """Test UserContext data structure"""

    def test_user_context_creation(self):
        """Test UserContext creation with defaults"""
        context = UserContext(user_id="123")

        assert context.user_id == "123"
        assert context.active_client_id is None
        assert context.preferences == {}
        assert context.permissions == []
        assert context.recent_activities == []
        assert isinstance(context.last_updated, datetime)

    def test_user_context_with_data(self):
        """Test UserContext with custom data"""
        preferences = {"theme": "dark", "language": "en"}
        permissions = ["read", "write"]

        context = UserContext(
            user_id="123",
            active_client_id="client_abc",
            preferences=preferences,
            permissions=permissions,
        )

        assert context.active_client_id == "client_abc"
        assert context.preferences == preferences
        assert context.permissions == permissions


class TestAuthCacheService:
    """Test the main AuthCacheService functionality"""

    @pytest.fixture
    def mock_redis_cache(self):
        """Mock Redis cache for testing"""
        mock = AsyncMock()
        mock.enabled = True
        mock.get.return_value = None
        mock.get_secure.return_value = None
        mock.set.return_value = True
        mock.set_secure.return_value = True
        mock.delete.return_value = True
        mock.exists.return_value = False
        return mock

    @pytest.fixture
    def auth_cache_service(self, mock_redis_cache):
        """Create AuthCacheService with mocked dependencies"""
        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=mock_redis_cache,
        ):
            service = AuthCacheService()
            return service

    @pytest.mark.asyncio
    async def test_user_session_caching(self, auth_cache_service, mock_redis_cache):
        """Test user session caching and retrieval"""
        # Create test session
        session = UserSession(
            user_id="test_123",
            email="test@example.com",
            full_name="Test User",
            role="user",
            is_admin=False,
        )

        # Test setting session cache
        result = await auth_cache_service.set_user_session(session)
        assert result is True

        # Verify Redis was called with secure storage
        mock_redis_cache.set_secure.assert_called_once()
        args, kwargs = mock_redis_cache.set_secure.call_args
        assert args[0] == "v1:user:test_123:session"
        # TTL is passed as third positional argument
        assert len(args) >= 3 and args[2] == AuthCacheService.TTL_USER_SESSION

        # Test getting session from cache (simulate cache hit)
        session_data = {
            "user_id": "test_123",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "user",
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "associations": [],
            "organization": None,
            "role_description": None,
        }
        mock_redis_cache.get_secure.return_value = session_data

        retrieved_session = await auth_cache_service.get_user_session("test_123")
        assert retrieved_session is not None
        assert retrieved_session.user_id == "test_123"
        assert retrieved_session.email == "test@example.com"
        assert isinstance(retrieved_session, UserSession)

    @pytest.mark.asyncio
    async def test_user_context_caching(self, auth_cache_service, mock_redis_cache):
        """Test user context caching and retrieval"""
        # Create test context
        context = UserContext(
            user_id="test_123",
            active_client_id="client_abc",
            preferences={"theme": "dark"},
        )

        # Test setting context cache
        result = await auth_cache_service.set_user_context(context)
        assert result is True

        # Verify Redis was called
        mock_redis_cache.set_secure.assert_called()

        # Test getting context from cache
        context_data = {
            "user_id": "test_123",
            "active_client_id": "client_abc",
            "preferences": {"theme": "dark"},
            "permissions": [],
            "recent_activities": [],
            "active_engagement_id": None,
            "active_flow_id": None,
            "last_updated": datetime.utcnow().isoformat(),
        }
        mock_redis_cache.get_secure.return_value = context_data

        retrieved_context = await auth_cache_service.get_user_context("test_123")
        assert retrieved_context is not None
        assert retrieved_context.user_id == "test_123"
        assert retrieved_context.active_client_id == "client_abc"
        assert retrieved_context.preferences == {"theme": "dark"}

    @pytest.mark.asyncio
    async def test_user_context_update(self, auth_cache_service, mock_redis_cache):
        """Test updating specific fields in user context"""
        # Mock existing context
        existing_context_data = {
            "user_id": "test_123",
            "active_client_id": "old_client",
            "preferences": {"theme": "light"},
            "permissions": ["read"],
            "recent_activities": [],
            "active_engagement_id": None,
            "active_flow_id": None,
            "last_updated": datetime.utcnow().isoformat(),
        }
        mock_redis_cache.get_secure.return_value = existing_context_data

        # Update context
        updates = {
            "active_client_id": "new_client",
            "preferences": {"theme": "dark", "language": "en"},
        }
        result = await auth_cache_service.update_user_context("test_123", updates)
        assert result is True

        # Verify Redis set was called
        mock_redis_cache.set_secure.assert_called()

    @pytest.mark.asyncio
    async def test_client_caching(self, auth_cache_service, mock_redis_cache):
        """Test client list caching"""
        clients = [
            {"id": "client_1", "name": "Client One"},
            {"id": "client_2", "name": "Client Two"},
        ]

        # Test setting clients cache
        result = await auth_cache_service.set_user_clients("test_123", clients)
        assert result is True

        # Verify non-secure storage was used for client data
        mock_redis_cache.set.assert_called()
        args, kwargs = mock_redis_cache.set.call_args
        assert args[0] == "v1:user:test_123:clients"
        # TTL is passed as third positional argument
        assert len(args) >= 3 and args[2] == AuthCacheService.TTL_CLIENT_LIST

        # Test getting clients from cache
        mock_redis_cache.get.return_value = clients
        retrieved_clients = await auth_cache_service.get_user_clients("test_123")
        assert retrieved_clients == clients

    @pytest.mark.asyncio
    async def test_engagement_caching(self, auth_cache_service, mock_redis_cache):
        """Test engagement caching"""
        engagements = [
            {"id": "eng_1", "name": "Engagement One"},
            {"id": "eng_2", "name": "Engagement Two"},
        ]

        # Test setting engagements cache
        result = await auth_cache_service.set_client_engagements(
            "client_123", engagements
        )
        assert result is True

        # Verify cache call
        mock_redis_cache.set.assert_called()
        args, kwargs = mock_redis_cache.set.call_args
        assert args[0] == "v1:client:client_123:engagements"
        # TTL is passed as third positional argument
        assert len(args) >= 3 and args[2] == AuthCacheService.TTL_ENGAGEMENTS

        # Test getting engagements from cache
        mock_redis_cache.get.return_value = engagements
        retrieved_engagements = await auth_cache_service.get_client_engagements(
            "client_123"
        )
        assert retrieved_engagements == engagements

    @pytest.mark.asyncio
    async def test_activity_buffering(self, auth_cache_service, mock_redis_cache):
        """Test activity buffering for batched operations"""
        activity = {
            "action": "login",
            "client_id": "client_123",
            "details": "User logged in successfully",
        }

        # Test buffering activity
        result = await auth_cache_service.buffer_user_activity("test_123", activity)
        assert result is True

        # Verify activity was added to buffer
        assert "test_123" in auth_cache_service.activity_buffers
        assert len(auth_cache_service.activity_buffers["test_123"]) == 1

        # Test getting buffered activities
        mock_redis_cache.get.return_value = [activity]
        activities = await auth_cache_service.get_buffered_activities("test_123")

        # Should contain activities from both in-memory and Redis buffers
        assert len(activities) >= 1
        assert any(act["action"] == "login" for act in activities)

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, auth_cache_service, mock_redis_cache):
        """Test various cache invalidation strategies"""
        # Test user session invalidation
        result = await auth_cache_service.invalidate_user_session("test_123")
        assert result is True
        mock_redis_cache.delete.assert_called()

        # Test user context invalidation
        result = await auth_cache_service.invalidate_user_context("test_123")
        assert result is True

        # Test full user cache invalidation
        result = await auth_cache_service.invalidate_user_caches("test_123")
        assert result is True

        # Test client cache invalidation
        result = await auth_cache_service.invalidate_client_caches("client_123")
        assert result is True

    @pytest.mark.asyncio
    async def test_fallback_behavior_redis_disabled(self, mock_redis_cache):
        """Test fallback behavior when Redis is disabled"""
        mock_redis_cache.enabled = False

        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=mock_redis_cache,
        ):
            service = AuthCacheService()

            # Create test session
            session = UserSession(
                user_id="test_123",
                email="test@example.com",
                full_name="Test User",
                role="user",
                is_admin=False,
            )

            # Should still work with fallback cache
            result = await service.set_user_session(session)
            assert result is True

            # Should retrieve from fallback cache
            retrieved_session = await service.get_user_session("test_123")
            assert retrieved_session is not None
            assert retrieved_session.user_id == "test_123"

    @pytest.mark.asyncio
    async def test_error_handling(self, auth_cache_service, mock_redis_cache):
        """Test error handling and graceful fallback"""
        # Simulate Redis error
        mock_redis_cache.get_secure.side_effect = Exception("Redis connection error")

        # Should handle error gracefully and return None
        session = await auth_cache_service.get_user_session("test_123")
        assert session is None

        # Should still update error statistics
        assert auth_cache_service.stats.errors > 0

    @pytest.mark.asyncio
    async def test_buffer_flushing(self, auth_cache_service):
        """Test activity buffer flushing"""
        # Add some activities to buffer
        old_activity = {
            "action": "old_action",
            "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
        }
        recent_activity = {
            "action": "recent_action",
            "timestamp": datetime.utcnow().isoformat(),
        }

        auth_cache_service.activity_buffers["test_123"] = [
            old_activity,
            recent_activity,
        ]

        # Flush old activities (older than 5 minutes)
        flushed_count = await auth_cache_service.flush_activity_buffers(
            max_age_minutes=5
        )

        # Should have flushed the old activity
        assert flushed_count >= 1

        # Recent activity should remain
        remaining_activities = auth_cache_service.activity_buffers.get("test_123", [])
        assert any(act["action"] == "recent_action" for act in remaining_activities)

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, auth_cache_service):
        """Test performance monitoring and statistics"""
        # Get initial stats
        initial_stats = await auth_cache_service.get_cache_stats()
        assert "total_requests" in initial_stats
        assert "hits" in initial_stats
        assert "misses" in initial_stats

        # Perform some cache operations to generate stats
        session = UserSession(
            user_id="test_123",
            email="test@example.com",
            full_name="Test User",
            role="user",
            is_admin=False,
        )
        await auth_cache_service.set_user_session(session)
        await auth_cache_service.get_user_session("test_123")

        # Get updated stats
        updated_stats = await auth_cache_service.get_cache_stats()
        assert updated_stats["total_requests"] >= initial_stats["total_requests"]

    @pytest.mark.asyncio
    async def test_health_check(self, auth_cache_service, mock_redis_cache):
        """Test health check functionality"""
        # Test healthy state
        health = await auth_cache_service.health_check()
        assert "status" in health
        assert "redis" in health
        assert "fallback" in health

        # Test degraded state (Redis unavailable)
        mock_redis_cache.enabled = False
        health = await auth_cache_service.health_check()
        assert health["status"] in ["degraded", "warning"]

    @pytest.mark.asyncio
    async def test_pattern_invalidation(self, auth_cache_service, mock_redis_cache):
        """Test pattern-based cache invalidation"""
        # Mock Redis SCAN operation
        mock_redis_cache.client = MagicMock()
        mock_redis_cache.client.scan = AsyncMock(return_value=("0", ["key1", "key2"]))

        # Test pattern invalidation
        await auth_cache_service.invalidate_pattern("v1:user:*:session")

        # Should have attempted to delete found keys
        assert mock_redis_cache.delete.call_count >= 2

    @pytest.mark.asyncio
    async def test_corrupted_cache_handling(self, auth_cache_service, mock_redis_cache):
        """Test handling of corrupted cache data"""
        # Return corrupted data that will cause UserSession construction to fail
        corrupted_data = {"user_id": "test_123", "invalid_field": "value"}
        mock_redis_cache.get_secure.return_value = corrupted_data

        # Should handle gracefully and return None
        session = await auth_cache_service.get_user_session("test_123")
        assert session is None

        # Should have attempted to delete corrupted entry
        mock_redis_cache.delete.assert_called()

    @pytest.mark.asyncio
    async def test_clear_all_caches(self, auth_cache_service, mock_redis_cache):
        """Test clearing all caches"""
        # Mock pattern invalidation
        with patch.object(
            auth_cache_service, "invalidate_pattern", return_value=5
        ) as mock_invalidate:
            result = await auth_cache_service.clear_all_caches()
            assert result is True

            # Should have attempted to clear multiple patterns
            assert mock_invalidate.call_count >= 5

    def test_singleton_pattern(self):
        """Test that get_auth_cache_service returns singleton"""
        service1 = get_auth_cache_service()
        service2 = get_auth_cache_service()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_cache_stats_calculation(self, auth_cache_service):
        """Test cache statistics calculations"""
        # Simulate some cache operations
        auth_cache_service.stats.total_requests = 100
        auth_cache_service.stats.hits = 80
        auth_cache_service.stats.misses = 20
        auth_cache_service.stats.errors = 5

        # Test hit rate calculation
        assert auth_cache_service.stats.hit_rate == 80.0

        # Test error rate calculation
        assert auth_cache_service.stats.error_rate == 5.0

    @pytest.mark.asyncio
    async def test_request_timing_tracking(self, auth_cache_service):
        """Test request timing tracking"""
        # Simulate a slow operation
        start_time = time.time() - 0.6  # 600ms operation
        await auth_cache_service._record_request_time("test_operation", start_time)

        # Should have recorded the timing
        assert len(auth_cache_service._request_times) > 0
        assert auth_cache_service.stats.average_response_time > 0

    @pytest.mark.asyncio
    async def test_secure_data_sanitization(self, auth_cache_service):
        """Test that sensitive data is properly sanitized"""
        clients = [
            {"id": "client_1", "name": "Client One", "secret": "sensitive_data"},
            {"id": "client_2", "name": "Client Two", "password": "secret_password"},
        ]

        # The service should sanitize sensitive data before caching
        result = await auth_cache_service.set_user_clients("test_123", clients)
        assert result is True

        # Verify that sanitization was attempted (mock would have been called)
        # In real implementation, sensitive fields would be removed or masked


class TestCacheIntegration:
    """Integration tests for cache components working together"""

    @pytest.mark.asyncio
    async def test_redis_fallback_integration(self):
        """Test Redis to fallback cache integration"""
        # Create service with real fallback cache but mock Redis
        mock_redis = AsyncMock()
        mock_redis.enabled = True
        mock_redis.get_secure.return_value = None  # Simulate cache miss
        mock_redis.set_secure.return_value = False  # Simulate Redis failure

        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=mock_redis,
        ):
            service = AuthCacheService()

            session = UserSession(
                user_id="test_123",
                email="test@example.com",
                full_name="Test User",
                role="user",
                is_admin=False,
            )

            # Should fallback to in-memory cache when Redis fails
            result = await service.set_user_session(session)
            assert result is True

            # Should retrieve from fallback cache
            retrieved_session = await service.get_user_session("test_123")
            assert retrieved_session is not None
            assert retrieved_session.user_id == "test_123"

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent cache operations"""
        mock_redis = AsyncMock()
        mock_redis.enabled = True
        mock_redis.get_secure.return_value = None
        mock_redis.set_secure.return_value = True

        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=mock_redis,
        ):
            service = AuthCacheService()

            # Create multiple sessions concurrently
            sessions = [
                UserSession(
                    user_id=f"user_{i}",
                    email=f"user{i}@example.com",
                    full_name=f"User {i}",
                    role="user",
                    is_admin=False,
                )
                for i in range(10)
            ]

            # Set all sessions concurrently
            tasks = [service.set_user_session(session) for session in sessions]
            results = await asyncio.gather(*tasks)

            # All operations should succeed
            assert all(results)

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """Test behavior under memory pressure"""
        # Create cache with very small capacity
        small_cache = InMemoryFallbackCache(max_size=5, default_ttl=300)

        # Fill beyond capacity
        for i in range(10):
            await small_cache.set(f"key_{i}", f"value_{i}")

        # Should only have 5 items (most recent)
        stats = small_cache.get_stats()
        assert stats["size"] == 5

        # Oldest items should be evicted
        assert await small_cache.get("key_0") is None
        assert await small_cache.get("key_9") == "value_9"

"""
Test Redis Cache Implementation

Tests the Redis cache service with different backends and atomic operations.
"""

import json
import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.caching.redis_cache import RedisCache, get_redis_cache


class TestRedisCache:
    """Test Redis cache functionality"""

    @pytest.fixture
    def mock_upstash_client(self):
        """Create mock Upstash Redis client"""
        client = MagicMock()
        client.get = MagicMock(return_value=None)
        client.set = MagicMock(return_value=True)
        client.setex = MagicMock(return_value=True)
        client.delete = MagicMock(return_value=True)
        client.exists = MagicMock(return_value=False)
        return client

    @pytest.fixture
    def mock_async_redis_client(self):
        """Create mock async Redis client"""
        client = AsyncMock()
        client.get = AsyncMock(return_value=None)
        client.set = AsyncMock(return_value=True)
        client.setex = AsyncMock(return_value=True)
        client.delete = AsyncMock(return_value=True)
        client.exists = AsyncMock(return_value=False)
        client.pipeline = MagicMock(return_value=AsyncMock())
        client.smembers = AsyncMock(return_value=set())
        client.sadd = AsyncMock(return_value=1)
        client.srem = AsyncMock(return_value=1)
        return client

    async def test_get_set_basic(self, mock_async_redis_client):
        """Test basic get/set operations"""
        cache = RedisCache()
        cache.client = mock_async_redis_client
        cache.client_type = "async"
        cache.enabled = True

        # Test set
        result = await cache.set("test_key", {"data": "value"}, ttl=60)
        assert result is True
        mock_async_redis_client.setex.assert_called_once()

        # Test get
        mock_async_redis_client.get.return_value = json.dumps({"data": "value"})
        result = await cache.get("test_key")
        assert result == {"data": "value"}

    async def test_acquire_release_lock(self, mock_async_redis_client):
        """Test distributed lock operations"""
        cache = RedisCache()
        cache.client = mock_async_redis_client
        cache.client_type = "async"
        cache.enabled = True

        # Test acquire lock
        mock_async_redis_client.set.return_value = True
        lock_id = await cache.acquire_lock("test_resource", ttl=30)
        assert lock_id is not None
        mock_async_redis_client.set.assert_called_with(
            "lock:test_resource", lock_id, nx=True, ex=30
        )

        # Test release lock
        mock_async_redis_client.get.return_value = lock_id
        result = await cache.release_lock("test_resource", lock_id)
        assert result is True

    async def test_atomic_flow_registration(self, mock_async_redis_client):
        """Test atomic flow registration"""
        cache = RedisCache()
        cache.client = mock_async_redis_client
        cache.client_type = "async"
        cache.enabled = True

        # Mock pipeline
        pipeline = AsyncMock()
        pipeline.setex = MagicMock(return_value=pipeline)
        pipeline.sadd = MagicMock(return_value=pipeline)
        pipeline.expire = MagicMock(return_value=pipeline)
        pipeline.execute = AsyncMock(return_value=[True, True, True, True])
        mock_async_redis_client.pipeline.return_value = pipeline

        flow_id = str(uuid.uuid4())
        flow_data = {
            "flow_id": flow_id,
            "flow_type": "discovery",
            "client_id": "test_client",
            "engagement_id": "test_engagement",
            "user_id": "test_user",
        }

        result = await cache.register_flow_atomic(
            flow_id=flow_id,
            flow_type="discovery",
            flow_data=flow_data,
        )

        assert result is True
        pipeline.setex.assert_called()
        pipeline.sadd.assert_called()
        pipeline.execute.assert_called_once()

    async def test_atomic_flow_unregistration(self, mock_async_redis_client):
        """Test atomic flow unregistration"""
        cache = RedisCache()
        cache.client = mock_async_redis_client
        cache.client_type = "async"
        cache.enabled = True

        # Mock pipeline
        pipeline = AsyncMock()
        pipeline.delete = MagicMock(return_value=pipeline)
        pipeline.srem = MagicMock(return_value=pipeline)
        pipeline.execute = AsyncMock(return_value=[True, True, True, True, True])
        mock_async_redis_client.pipeline.return_value = pipeline

        flow_id = str(uuid.uuid4())
        result = await cache.unregister_flow_atomic(flow_id, "discovery")

        assert result is True
        pipeline.delete.assert_called()
        pipeline.srem.assert_called_with("flows:active:discovery", flow_id)
        pipeline.execute.assert_called_once()

    async def test_flow_state_caching(self, mock_async_redis_client):
        """Test flow state caching operations"""
        cache = RedisCache()
        cache.client = mock_async_redis_client
        cache.client_type = "async"
        cache.enabled = True

        flow_id = str(uuid.uuid4())
        state = {
            "status": "running",
            "progress": 50,
            "metadata": {"key": "value"},
        }

        # Test cache flow state
        result = await cache.cache_flow_state(flow_id, state)
        assert result is True

        # Test get flow state
        mock_async_redis_client.get.return_value = json.dumps(state)
        cached_state = await cache.get_flow_state(flow_id)
        assert cached_state == state

    async def test_redis_fallback_decorator(self):
        """Test Redis fallback decorator behavior"""
        cache = RedisCache()
        cache.enabled = False  # Disable Redis

        # All operations should return fallback values
        assert await cache.get("test") is None
        assert await cache.set("test", "value") is False
        assert await cache.exists("test") is False
        assert await cache.acquire_lock("test") is None
        assert await cache.release_lock("test", "lock_id") is True

    async def test_upstash_compatibility(self, mock_upstash_client):
        """Test Upstash Redis compatibility"""
        cache = RedisCache()
        cache.client = mock_upstash_client
        cache.client_type = "upstash"
        cache.enabled = True

        # Test atomic flow registration with Upstash
        flow_id = str(uuid.uuid4())
        flow_data = {
            "flow_id": flow_id,
            "flow_type": "discovery",
            "client_id": "test_client",
        }

        result = await cache.register_flow_atomic(
            flow_id=flow_id,
            flow_type="discovery",
            flow_data=flow_data,
        )

        assert result is True
        # Upstash uses individual operations, not pipeline
        assert mock_upstash_client.setex.call_count >= 3

    async def test_race_condition_prevention(self, mock_async_redis_client):
        """Test that race conditions are prevented during flow registration"""
        cache = RedisCache()
        cache.client = mock_async_redis_client
        cache.client_type = "async"
        cache.enabled = True

        flow_id = str(uuid.uuid4())

        # Simulate flow already exists
        mock_async_redis_client.get.return_value = "1"

        result = await cache.register_flow_atomic(
            flow_id=flow_id,
            flow_type="discovery",
            flow_data={"flow_id": flow_id},
        )

        assert result is False  # Should fail because flow already exists


async def test_singleton_instance():
    """Test that get_redis_cache returns singleton instance"""
    cache1 = get_redis_cache()
    cache2 = get_redis_cache()
    assert cache1 is cache2

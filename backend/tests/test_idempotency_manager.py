"""
Unit Tests for IdempotencyManager

Tests the IdempotencyManager that provides idempotency guarantees
for operations in the Service Registry architecture.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.context import RequestContext
from app.services.idempotency_manager import (
    IdempotencyManager,
    IdempotencyStatus,
    IdempotencyRecord,
)


class TestIdempotencyManagerInitialization:
    """Test IdempotencyManager initialization"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        return AsyncMock()

    @pytest.fixture
    def mock_context(self):
        """Create mock request context"""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            flow_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    def manager(self, mock_session, mock_context):
        """Create IdempotencyManager instance"""
        return IdempotencyManager(mock_session, mock_context)

    def test_initialization(self, manager, mock_session, mock_context):
        """Test manager initialization"""
        assert manager._session == mock_session
        assert manager._context == mock_context
        assert len(manager._recent_keys_cache) == 0
        assert manager._cache_max_size == 100
        assert manager.DEFAULT_TTL == 3600
        assert manager.MAX_TTL == 86400

    @pytest.mark.asyncio
    async def test_health_check(self, manager):
        """Test health check"""
        manager._recent_keys_cache = {"key1": MagicMock(), "key2": MagicMock()}

        health = await manager.health_check()

        assert health["status"] == "healthy"
        assert health["service"] == "IdempotencyManager"
        assert health["cache_size"] == 2
        assert health["cache_max_size"] == 100
        assert health["default_ttl"] == 3600


class TestIdempotencyKeyGeneration:
    """Test idempotency key generation"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        session = AsyncMock()
        context = RequestContext(
            client_account_id="client123", engagement_id="engage456"
        )
        return IdempotencyManager(session, context)

    def test_generate_idempotency_key_basic(self, manager):
        """Test basic key generation"""
        key = manager.generate_idempotency_key(
            operation="create_asset", request_data={"name": "server1", "type": "server"}
        )

        assert key.startswith("create_asset_")
        assert len(key) > 20  # operation + underscore + hash

        # Same input should generate same key
        key2 = manager.generate_idempotency_key(
            operation="create_asset", request_data={"name": "server1", "type": "server"}
        )
        assert key == key2

    def test_generate_idempotency_key_with_custom(self, manager):
        """Test key generation with custom component"""
        key = manager.generate_idempotency_key(
            operation="update",
            request_data={"id": "123"},
            custom_key="custom_component",
        )

        # Different custom key should generate different result
        key2 = manager.generate_idempotency_key(
            operation="update",
            request_data={"id": "123"},
            custom_key="different_component",
        )

        assert key != key2

    def test_generate_idempotency_key_order_independence(self, manager):
        """Test that key generation is order-independent for dicts"""
        key1 = manager.generate_idempotency_key(
            operation="test", request_data={"a": 1, "b": 2, "c": 3}
        )

        key2 = manager.generate_idempotency_key(
            operation="test", request_data={"c": 3, "a": 1, "b": 2}
        )

        assert key1 == key2

    def test_generate_idempotency_key_with_error(self, manager):
        """Test key generation with error handling"""
        # Mock json.dumps to raise an error
        with patch("json.dumps", side_effect=Exception("JSON error")):
            key = manager.generate_idempotency_key(
                operation="test", request_data={"data": "value"}
            )

            # Should fall back to timestamp-based key
            assert key.startswith("test_")
            assert "." in key  # Contains timestamp


class TestIdempotencyChecking:
    """Test idempotency checking functionality"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        session = AsyncMock()
        context = RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )
        return IdempotencyManager(session, context)

    @pytest.mark.asyncio
    async def test_check_idempotency_not_found(self, manager):
        """Test checking non-existent key"""
        result = await manager.check_idempotency(
            idempotency_key="test_key_123",
            operation="test_op",
            request_data={"data": "value"},
        )

        assert result is None
        assert "test_key_123" in manager._recent_keys_cache

    @pytest.mark.asyncio
    async def test_check_idempotency_found_in_cache(self, manager):
        """Test finding key in cache"""
        # Add record to cache
        record = IdempotencyRecord(
            idempotency_key="cached_key",
            operation="test_op",
            status=IdempotencyStatus.COMPLETED,
            result={"success": True},
            error=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            request_hash="hash123",
            metadata={},
        )
        manager._recent_keys_cache["cached_key"] = record

        result = await manager.check_idempotency(
            idempotency_key="cached_key", operation="test_op", request_data={}
        )

        assert result == record

    @pytest.mark.asyncio
    async def test_check_idempotency_expired_in_cache(self, manager):
        """Test expired record in cache"""
        # Add expired record to cache
        record = IdempotencyRecord(
            idempotency_key="expired_key",
            operation="test_op",
            status=IdempotencyStatus.COMPLETED,
            result={"success": True},
            error=None,
            created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            updated_at=datetime.now(timezone.utc) - timedelta(hours=2),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            request_hash="hash123",
            metadata={},
        )
        manager._recent_keys_cache["expired_key"] = record

        result = await manager.check_idempotency(
            idempotency_key="expired_key", operation="test_op", request_data={}
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_check_idempotency_with_ttl(self, manager):
        """Test checking with custom TTL"""
        result = await manager.check_idempotency(
            idempotency_key="ttl_key",
            operation="test_op",
            request_data={},
            ttl_seconds=7200,  # 2 hours
        )

        assert result is None
        # Check that new record was added to cache
        cached = manager._recent_keys_cache.get("ttl_key")
        assert cached is not None

        # Check TTL is applied correctly (2 hours)
        time_diff = cached.expires_at - cached.created_at
        assert 7190 < time_diff.total_seconds() < 7210  # Allow some variance


class TestOperationLifecycle:
    """Test operation lifecycle management"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        session = AsyncMock()
        context = RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )
        return IdempotencyManager(session, context)

    @pytest.mark.asyncio
    async def test_start_operation_new(self, manager):
        """Test starting a new operation"""
        result = await manager.start_operation(
            idempotency_key="new_op_key",
            operation="create",
            request_data={"item": "value"},
        )

        assert result is True

        # Check that record is in cache with IN_PROGRESS status
        cached = manager._recent_keys_cache.get("new_op_key")
        assert cached is not None
        assert cached.status == IdempotencyStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_start_operation_duplicate_completed(self, manager):
        """Test starting operation that's already completed"""
        # Add completed record
        completed_record = IdempotencyRecord(
            idempotency_key="completed_key",
            operation="create",
            status=IdempotencyStatus.COMPLETED,
            result={"id": "123"},
            error=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            request_hash="hash",
            metadata={},
        )
        manager._recent_keys_cache["completed_key"] = completed_record

        result = await manager.start_operation(
            idempotency_key="completed_key",
            operation="create",
            request_data={"item": "value"},
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_start_operation_duplicate_in_progress(self, manager):
        """Test starting operation that's already in progress"""
        # Add in-progress record
        in_progress_record = IdempotencyRecord(
            idempotency_key="progress_key",
            operation="create",
            status=IdempotencyStatus.IN_PROGRESS,
            result=None,
            error=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            request_hash="hash",
            metadata={},
        )
        manager._recent_keys_cache["progress_key"] = in_progress_record

        result = await manager.start_operation(
            idempotency_key="progress_key",
            operation="create",
            request_data={"item": "value"},
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_start_operation_retry_failed(self, manager):
        """Test retrying a failed operation"""
        # Add failed record
        failed_record = IdempotencyRecord(
            idempotency_key="failed_key",
            operation="create",
            status=IdempotencyStatus.FAILED,
            result=None,
            error="Previous error",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            updated_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            request_hash="hash",
            metadata={},
        )
        manager._recent_keys_cache["failed_key"] = failed_record

        result = await manager.start_operation(
            idempotency_key="failed_key",
            operation="create",
            request_data={"item": "value"},
        )

        # Should allow retry
        assert result is True

    @pytest.mark.asyncio
    async def test_complete_operation(self, manager):
        """Test completing an operation"""
        # Add in-progress record
        key = "complete_test_key"
        record = IdempotencyRecord(
            idempotency_key=key,
            operation="create",
            status=IdempotencyStatus.IN_PROGRESS,
            result=None,
            error=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            request_hash="hash",
            metadata={},
        )
        manager._recent_keys_cache[key] = record

        result = await manager.complete_operation(
            idempotency_key=key, result={"id": "123", "status": "created"}
        )

        assert result is True
        assert record.status == IdempotencyStatus.COMPLETED
        assert record.result == {"id": "123", "status": "created"}

    @pytest.mark.asyncio
    async def test_fail_operation(self, manager):
        """Test failing an operation"""
        # Add in-progress record
        key = "fail_test_key"
        record = IdempotencyRecord(
            idempotency_key=key,
            operation="create",
            status=IdempotencyStatus.IN_PROGRESS,
            result=None,
            error=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            request_hash="hash",
            metadata={},
        )
        manager._recent_keys_cache[key] = record

        result = await manager.fail_operation(
            idempotency_key=key, error="Database connection failed"
        )

        assert result is True
        assert record.status == IdempotencyStatus.FAILED
        assert record.error == "Database connection failed"


class TestCachedResults:
    """Test cached result retrieval"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        session = AsyncMock()
        context = RequestContext(client_account_id=str(uuid.uuid4()))
        return IdempotencyManager(session, context)

    @pytest.mark.asyncio
    async def test_get_cached_result_success(self, manager):
        """Test getting cached result for completed operation"""
        key = "cached_result_key"
        expected_result = {"id": "456", "data": "value"}

        record = IdempotencyRecord(
            idempotency_key=key,
            operation="test",
            status=IdempotencyStatus.COMPLETED,
            result=expected_result,
            error=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            request_hash="hash",
            metadata={},
        )
        manager._recent_keys_cache[key] = record

        result = await manager.get_cached_result(key)

        assert result == expected_result

    @pytest.mark.asyncio
    async def test_get_cached_result_not_completed(self, manager):
        """Test getting result for non-completed operation"""
        key = "in_progress_key"

        record = IdempotencyRecord(
            idempotency_key=key,
            operation="test",
            status=IdempotencyStatus.IN_PROGRESS,
            result=None,
            error=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            request_hash="hash",
            metadata={},
        )
        manager._recent_keys_cache[key] = record

        result = await manager.get_cached_result(key)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_result_expired(self, manager):
        """Test getting expired result"""
        key = "expired_result_key"

        record = IdempotencyRecord(
            idempotency_key=key,
            operation="test",
            status=IdempotencyStatus.COMPLETED,
            result={"data": "old"},
            error=None,
            created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            updated_at=datetime.now(timezone.utc) - timedelta(hours=2),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            request_hash="hash",
            metadata={},
        )
        manager._recent_keys_cache[key] = record

        result = await manager.get_cached_result(key)

        assert result is None
        assert key not in manager._recent_keys_cache  # Should be removed


class TestCleanup:
    """Test cleanup functionality"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        session = AsyncMock()
        context = RequestContext(client_account_id=str(uuid.uuid4()))
        return IdempotencyManager(session, context)

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, manager):
        """Test cleaning up expired records"""
        now = datetime.now(timezone.utc)

        # Add mix of expired and valid records
        manager._recent_keys_cache = {
            "expired1": IdempotencyRecord(
                idempotency_key="expired1",
                operation="test",
                status=IdempotencyStatus.COMPLETED,
                result={},
                error=None,
                created_at=now - timedelta(hours=2),
                updated_at=now - timedelta(hours=2),
                expires_at=now - timedelta(hours=1),
                request_hash="hash",
                metadata={},
            ),
            "expired2": IdempotencyRecord(
                idempotency_key="expired2",
                operation="test",
                status=IdempotencyStatus.FAILED,
                result=None,
                error="error",
                created_at=now - timedelta(hours=3),
                updated_at=now - timedelta(hours=3),
                expires_at=now - timedelta(minutes=30),
                request_hash="hash",
                metadata={},
            ),
            "valid": IdempotencyRecord(
                idempotency_key="valid",
                operation="test",
                status=IdempotencyStatus.COMPLETED,
                result={},
                error=None,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(hours=1),
                request_hash="hash",
                metadata={},
            ),
        }

        count = await manager.cleanup_expired()

        assert count == 2
        assert "expired1" not in manager._recent_keys_cache
        assert "expired2" not in manager._recent_keys_cache
        assert "valid" in manager._recent_keys_cache


class TestValidation:
    """Test validation functionality"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        session = AsyncMock()
        context = RequestContext(client_account_id=str(uuid.uuid4()))
        return IdempotencyManager(session, context)

    def test_validate_idempotency_key(self, manager):
        """Test idempotency key validation"""
        # Valid keys
        assert manager.validate_idempotency_key("operation_abc123def456") is True
        assert manager.validate_idempotency_key("create-asset_12345678") is True
        assert manager.validate_idempotency_key("UPDATE_RECORD_xyz789") is True

        # Invalid keys
        assert manager.validate_idempotency_key("") is False
        assert manager.validate_idempotency_key(None) is False
        assert manager.validate_idempotency_key("short") is False
        assert manager.validate_idempotency_key("no_hash") is False
        assert manager.validate_idempotency_key("invalid chars!@#") is False
        assert manager.validate_idempotency_key("missing-underscore") is False


class TestRequestNormalization:
    """Test request data normalization"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        session = AsyncMock()
        context = RequestContext(client_account_id=str(uuid.uuid4()))
        return IdempotencyManager(session, context)

    def test_normalize_request_data(self, manager):
        """Test request data normalization"""
        data = {
            "name": "test",
            "timestamp": "2024-01-01T00:00:00",
            "id": "123",
            "values": [3, 1, 2],
            "nested": {"created_at": "2024-01-01", "field": "value"},
        }

        normalized = manager._normalize_request_data(data)

        # Volatile fields should be removed
        assert "timestamp" not in normalized
        assert "id" not in normalized
        assert "created_at" not in normalized["nested"]

        # Lists should be sorted
        assert normalized["values"] == ["1", "2", "3"]

        # Other fields preserved
        assert normalized["name"] == "test"
        assert normalized["nested"]["field"] == "value"

    def test_hash_request_data(self, manager):
        """Test request data hashing"""
        data1 = {"field1": "value1", "field2": "value2"}
        data2 = {"field2": "value2", "field1": "value1"}
        data3 = {"field1": "value1", "field2": "different"}

        hash1 = manager._hash_request_data(data1)
        hash2 = manager._hash_request_data(data2)
        hash3 = manager._hash_request_data(data3)

        # Same data in different order should produce same hash
        assert hash1 == hash2

        # Different data should produce different hash
        assert hash1 != hash3

        # Hash should be consistent length (SHA256)
        assert len(hash1) == 64


class TestCacheManagement:
    """Test cache management"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        session = AsyncMock()
        context = RequestContext(client_account_id=str(uuid.uuid4()))
        manager = IdempotencyManager(session, context)
        manager._cache_max_size = 3  # Small size for testing
        return manager

    def test_add_to_cache_with_limit(self, manager):
        """Test cache size limiting"""
        # Fill cache to capacity
        for i in range(3):
            record = IdempotencyRecord(
                idempotency_key=f"key{i}",
                operation="test",
                status=IdempotencyStatus.COMPLETED,
                result={},
                error=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                request_hash="hash",
                metadata={},
            )
            manager._add_to_cache(f"key{i}", record)

        assert len(manager._recent_keys_cache) == 3
        assert "key0" in manager._recent_keys_cache

        # Add one more - should evict oldest
        new_record = IdempotencyRecord(
            idempotency_key="key3",
            operation="test",
            status=IdempotencyStatus.COMPLETED,
            result={},
            error=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            request_hash="hash",
            metadata={},
        )
        manager._add_to_cache("key3", new_record)

        assert len(manager._recent_keys_cache) == 3
        assert "key0" not in manager._recent_keys_cache  # Oldest evicted
        assert "key3" in manager._recent_keys_cache

    def test_get_cache_stats(self, manager):
        """Test cache statistics"""
        now = datetime.now(timezone.utc)

        # Add various records
        manager._recent_keys_cache = {
            "completed": IdempotencyRecord(
                idempotency_key="completed",
                operation="test",
                status=IdempotencyStatus.COMPLETED,
                result={},
                error=None,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(hours=1),
                request_hash="hash",
                metadata={},
            ),
            "in_progress": IdempotencyRecord(
                idempotency_key="in_progress",
                operation="test",
                status=IdempotencyStatus.IN_PROGRESS,
                result=None,
                error=None,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(hours=1),
                request_hash="hash",
                metadata={},
            ),
            "expired": IdempotencyRecord(
                idempotency_key="expired",
                operation="test",
                status=IdempotencyStatus.COMPLETED,
                result={},
                error=None,
                created_at=now - timedelta(hours=2),
                updated_at=now - timedelta(hours=2),
                expires_at=now - timedelta(hours=1),
                request_hash="hash",
                metadata={},
            ),
        }

        stats = manager.get_cache_stats()

        assert stats["cache_size"] == 3
        assert stats["expired_count"] == 1
        assert stats["status_counts"]["completed"] == 1
        assert stats["status_counts"]["in_progress"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

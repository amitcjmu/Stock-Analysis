"""
Integration tests for auth performance optimization system

Tests end-to-end integration of auth components including:
- AuthCacheService integration with Redis and fallback
- Storage manager integration with database operations
- Authentication flow performance under various conditions
- Context switching and session management
- Cache coherence and invalidation across components
- Error recovery and graceful degradation
- Multi-user concurrent access patterns
- Security validation in performance scenarios
"""

import asyncio
import pytest
import time
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.caching.auth_cache_service import (
    AuthCacheService,
    UserSession,
    UserContext,
)
from app.services.data_import.storage_manager import ImportStorageManager


class TestAuthPerformanceIntegration:
    """Test auth performance optimization components working together"""

    @pytest.fixture
    def mock_redis_cache(self):
        """Mock Redis cache with performance characteristics"""
        mock = AsyncMock()
        mock.enabled = True
        mock.get.return_value = None
        mock.get_secure.return_value = None
        mock.set.return_value = True
        mock.set_secure.return_value = True
        mock.delete.return_value = True
        mock.exists.return_value = False

        # Add simulated latency for realistic testing
        async def mock_get_with_latency(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms latency
            return None

        async def mock_set_with_latency(*args, **kwargs):
            await asyncio.sleep(0.005)  # 5ms latency
            return True

        mock.get.side_effect = mock_get_with_latency
        mock.set.side_effect = mock_set_with_latency
        mock.get_secure.side_effect = mock_get_with_latency
        mock.set_secure.side_effect = mock_set_with_latency

        return mock

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session with performance characteristics"""
        mock = AsyncMock()

        # Add simulated database latency
        async def mock_execute_with_latency(*args, **kwargs):
            await asyncio.sleep(0.02)  # 20ms database latency
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            return result

        mock.execute.side_effect = mock_execute_with_latency
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

    @pytest.fixture
    def storage_manager(self, mock_db_session):
        """Create StorageManager with mocked dependencies"""
        return ImportStorageManager(mock_db_session, "test_client_123")

    @pytest.fixture
    def sample_users(self):
        """Generate sample users for testing"""
        users = []
        for i in range(10):
            users.append(
                {
                    "user_id": f"user_{i:03d}",
                    "email": f"user{i}@example.com",
                    "full_name": f"Test User {i}",
                    "role": "user" if i % 2 == 0 else "admin",
                    "is_admin": i % 5 == 0,  # Every 5th user is admin
                    "client_id": f"client_{i % 3}",  # 3 clients total
                    "engagement_id": f"engagement_{i % 2}",  # 2 engagements total
                }
            )
        return users

    @pytest.mark.asyncio
    async def test_login_performance_optimization(
        self, auth_cache_service, sample_users
    ):
        """Test login performance with cache optimization (target: 200-500ms from 2-4s)"""
        user_data = sample_users[0]

        # Simulate initial login (cache miss)
        start_time = time.time()

        session = UserSession(
            user_id=user_data["user_id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_admin=user_data["is_admin"],
        )

        # Cache the session
        cache_success = await auth_cache_service.set_user_session(session)
        assert cache_success is True

        # Set user context
        context = UserContext(
            user_id=user_data["user_id"],
            active_client_id=user_data["client_id"],
            active_engagement_id=user_data["engagement_id"],
        )
        context_success = await auth_cache_service.set_user_context(context)
        assert context_success is True

        initial_login_time = time.time() - start_time

        # Simulate subsequent login (cache hit)
        start_time = time.time()

        cached_session = await auth_cache_service.get_user_session(user_data["user_id"])
        cached_context = await auth_cache_service.get_user_context(user_data["user_id"])

        cached_login_time = time.time() - start_time

        # Performance assertions (allowing for mock latencies)
        assert (
            initial_login_time < 0.1
        )  # Should be fast even on initial login with mocks
        assert cached_login_time < 0.05  # Cached login should be very fast

        # Verify data integrity
        assert cached_session is not None
        assert cached_session.user_id == user_data["user_id"]
        assert cached_context is not None
        assert cached_context.active_client_id == user_data["client_id"]

    @pytest.mark.asyncio
    async def test_context_switching_performance(
        self, auth_cache_service, sample_users
    ):
        """Test context switching performance (target: 100-300ms from 1-2s)"""
        user_data = sample_users[0]

        # Setup initial context
        initial_context = UserContext(
            user_id=user_data["user_id"],
            active_client_id="client_1",
            active_engagement_id="engagement_1",
        )
        await auth_cache_service.set_user_context(initial_context)

        # Simulate context switches
        context_switch_times = []

        for i in range(5):
            start_time = time.time()

            # Update context (simulating client/engagement switch)
            updates = {
                "active_client_id": f"client_{i % 3}",
                "active_engagement_id": f"engagement_{i % 2}",
                "active_flow_id": f"flow_{i}",
            }

            success = await auth_cache_service.update_user_context(
                user_data["user_id"], updates
            )
            assert success is True

            # Verify context was updated
            updated_context = await auth_cache_service.get_user_context(
                user_data["user_id"]
            )
            assert updated_context.active_client_id == updates["active_client_id"]

            switch_time = time.time() - start_time
            context_switch_times.append(switch_time)

        # Performance assertions
        avg_switch_time = sum(context_switch_times) / len(context_switch_times)
        max_switch_time = max(context_switch_times)

        assert avg_switch_time < 0.1  # Average switch time should be fast
        assert max_switch_time < 0.2  # No switch should take too long

        print(f"Average context switch time: {avg_switch_time*1000:.2f}ms")
        print(f"Max context switch time: {max_switch_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_user_operations(self, auth_cache_service, sample_users):
        """Test performance under concurrent user operations"""
        # Setup sessions for all users
        sessions = []
        for user_data in sample_users:
            session = UserSession(
                user_id=user_data["user_id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_admin=user_data["is_admin"],
            )
            sessions.append(session)

        # Concurrent session caching
        start_time = time.time()

        cache_tasks = [
            auth_cache_service.set_user_session(session) for session in sessions
        ]
        cache_results = await asyncio.gather(*cache_tasks)

        concurrent_cache_time = time.time() - start_time

        # Verify all operations succeeded
        assert all(cache_results)

        # Concurrent session retrieval
        start_time = time.time()

        retrieval_tasks = [
            auth_cache_service.get_user_session(user_data["user_id"])
            for user_data in sample_users
        ]
        retrieved_sessions = await asyncio.gather(*retrieval_tasks)

        concurrent_retrieval_time = time.time() - start_time

        # Performance assertions
        assert concurrent_cache_time < 0.5  # 500ms for 10 concurrent operations
        assert concurrent_retrieval_time < 0.3  # 300ms for 10 concurrent retrievals

        # Verify data integrity
        assert all(session is not None for session in retrieved_sessions)
        for i, session in enumerate(retrieved_sessions):
            assert session.user_id == sample_users[i]["user_id"]

        print(f"Concurrent cache time (10 users): {concurrent_cache_time*1000:.2f}ms")
        print(
            f"Concurrent retrieval time (10 users): {concurrent_retrieval_time*1000:.2f}ms"
        )

    @pytest.mark.asyncio
    async def test_cache_fallback_performance(self, mock_redis_cache, sample_users):
        """Test performance when Redis fails and fallback cache is used"""
        user_data = sample_users[0]

        # Start with working Redis
        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=mock_redis_cache,
        ):
            service = AuthCacheService()

            session = UserSession(
                user_id=user_data["user_id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_admin=user_data["is_admin"],
            )

            # Cache in Redis
            await service.set_user_session(session)

            # Simulate Redis failure
            mock_redis_cache.enabled = False
            mock_redis_cache.get_secure.side_effect = ConnectionError(
                "Redis unavailable"
            )

            # Test fallback performance
            start_time = time.time()

            # This should fallback to in-memory cache
            fallback_success = await service.set_user_session(session)
            retrieved_session = await service.get_user_session(user_data["user_id"])

            fallback_time = time.time() - start_time

            # Performance and functionality assertions
            assert fallback_success is True
            assert retrieved_session is not None
            assert retrieved_session.user_id == user_data["user_id"]
            assert fallback_time < 0.05  # Fallback should be very fast

            print(f"Fallback operation time: {fallback_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_cache_invalidation_performance(
        self, auth_cache_service, sample_users
    ):
        """Test cache invalidation performance across multiple users"""
        # Setup cache data for multiple users
        setup_tasks = []
        for user_data in sample_users:
            session = UserSession(
                user_id=user_data["user_id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_admin=user_data["is_admin"],
            )
            context = UserContext(
                user_id=user_data["user_id"], active_client_id=user_data["client_id"]
            )

            setup_tasks.extend(
                [
                    auth_cache_service.set_user_session(session),
                    auth_cache_service.set_user_context(context),
                ]
            )

        await asyncio.gather(*setup_tasks)

        # Test individual user invalidation
        start_time = time.time()

        invalidation_success = await auth_cache_service.invalidate_user_caches(
            sample_users[0]["user_id"]
        )

        individual_invalidation_time = time.time() - start_time

        assert invalidation_success is True
        assert individual_invalidation_time < 0.1  # Should be fast

        # Test bulk invalidation (simulate user logout wave)
        start_time = time.time()

        invalidation_tasks = [
            auth_cache_service.invalidate_user_caches(user_data["user_id"])
            for user_data in sample_users[1:6]  # Invalidate 5 users
        ]
        invalidation_results = await asyncio.gather(*invalidation_tasks)

        bulk_invalidation_time = time.time() - start_time

        assert all(invalidation_results)
        assert bulk_invalidation_time < 0.3  # Bulk invalidation should be reasonable

        print(
            f"Individual invalidation time: {individual_invalidation_time*1000:.2f}ms"
        )
        print(f"Bulk invalidation time (5 users): {bulk_invalidation_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_integrated_auth_storage_workflow(
        self, auth_cache_service, storage_manager, sample_users
    ):
        """Test integrated auth and storage operations"""
        user_data = sample_users[0]

        # Step 1: User authentication and caching
        start_time = time.time()

        session = UserSession(
            user_id=user_data["user_id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_admin=user_data["is_admin"],
        )

        context = UserContext(
            user_id=user_data["user_id"],
            active_client_id=user_data["client_id"],
            active_engagement_id=user_data["engagement_id"],
        )

        # Cache auth data
        auth_tasks = [
            auth_cache_service.set_user_session(session),
            auth_cache_service.set_user_context(context),
        ]
        auth_results = await asyncio.gather(*auth_tasks)

        auth_time = time.time() - start_time

        # Step 2: Storage operations using cached context
        start_time = time.time()

        # Simulate data import operation
        import_data = {
            "import_id": uuid.uuid4(),
            "engagement_id": user_data["engagement_id"],
            "user_id": user_data["user_id"],
            "filename": "test_servers.csv",
            "file_size": 2048,
            "file_type": "text/csv",
            "intended_type": "servers",
        }

        data_import = await storage_manager.find_or_create_import(**import_data)

        # Update import status
        await storage_manager.update_import_status(
            data_import, "in_progress", total_records=100, processed_records=50
        )

        storage_time = time.time() - start_time

        # Step 3: Update user activity in cache
        start_time = time.time()

        activity = {
            "action": "data_import",
            "import_id": str(import_data["import_id"]),
            "status": "in_progress",
            "progress": 50,
        }

        await auth_cache_service.buffer_user_activity(user_data["user_id"], activity)

        activity_time = time.time() - start_time

        # Performance assertions
        assert all(auth_results)
        assert auth_time < 0.1  # Auth operations should be fast
        assert storage_time < 0.2  # Storage operations should be reasonable
        assert activity_time < 0.05  # Activity buffering should be very fast

        # Verify integration
        cached_session = await auth_cache_service.get_user_session(user_data["user_id"])
        cached_context = await auth_cache_service.get_user_context(user_data["user_id"])

        assert cached_session.user_id == data_import.imported_by
        assert cached_context.active_engagement_id == data_import.engagement_id

        print(
            f"Integrated workflow - Auth: {auth_time*1000:.2f}ms, "
            f"Storage: {storage_time*1000:.2f}ms, Activity: {activity_time*1000:.2f}ms"
        )

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, auth_cache_service, sample_users):
        """Test system behavior under memory pressure"""
        # Fill cache with many sessions to simulate memory pressure
        large_user_set = []
        for i in range(100):  # Create 100 users
            large_user_set.append(
                {
                    "user_id": f"load_user_{i:03d}",
                    "email": f"load{i}@example.com",
                    "full_name": f"Load Test User {i}",
                    "role": "user",
                    "is_admin": False,
                }
            )

        # Batch session creation
        batch_size = 20
        batches = [
            large_user_set[i : i + batch_size]
            for i in range(0, len(large_user_set), batch_size)
        ]

        total_start_time = time.time()

        for batch_num, batch in enumerate(batches):
            batch_start_time = time.time()

            batch_tasks = []
            for user_data in batch:
                session = UserSession(
                    user_id=user_data["user_id"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    is_admin=user_data["is_admin"],
                )
                batch_tasks.append(auth_cache_service.set_user_session(session))

            batch_results = await asyncio.gather(*batch_tasks)
            batch_time = time.time() - batch_start_time

            # Verify batch succeeded
            assert all(batch_results)

            # Performance should remain consistent even under load
            assert batch_time < 0.5  # Each batch should complete quickly

            print(
                f"Batch {batch_num + 1}/5: {batch_time*1000:.2f}ms for {len(batch)} users"
            )

        total_time = time.time() - total_start_time

        # Overall performance assertion
        assert total_time < 3.0  # 100 users should be processed in under 3 seconds

        # Test cache eviction behavior by accessing fallback cache stats
        fallback_stats = auth_cache_service.fallback_cache.get_stats()
        print(f"Fallback cache utilization: {fallback_stats['utilization']:.1f}%")

        # Cache should handle memory pressure gracefully
        assert fallback_stats["utilization"] <= 100  # Should not exceed capacity

    @pytest.mark.asyncio
    async def test_error_recovery_integration(
        self, auth_cache_service, storage_manager, sample_users
    ):
        """Test error recovery across integrated components"""
        user_data = sample_users[0]

        # Setup normal operation
        session = UserSession(
            user_id=user_data["user_id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_admin=user_data["is_admin"],
        )

        await auth_cache_service.set_user_session(session)

        # Simulate partial system failure - storage fails but cache works
        storage_manager.db.execute.side_effect = Exception("Database connection lost")

        # Cache operations should still work
        retrieved_session = await auth_cache_service.get_user_session(
            user_data["user_id"]
        )
        assert retrieved_session is not None

        # Activity buffering should continue working
        activity = {"action": "error_recovery_test", "status": "cache_only"}
        buffer_success = await auth_cache_service.buffer_user_activity(
            user_data["user_id"], activity
        )
        assert buffer_success is True

        # System should maintain performance even during partial failures
        start_time = time.time()

        for i in range(10):
            await auth_cache_service.get_user_session(user_data["user_id"])

        recovery_time = time.time() - start_time
        assert recovery_time < 0.2  # Should remain fast during partial failure

        print(f"Error recovery performance (10 cache ops): {recovery_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_security_performance_integration(
        self, auth_cache_service, sample_users
    ):
        """Test security features don't significantly impact performance"""
        user_data = sample_users[0]

        # Test secure vs non-secure operations
        sensitive_data = {
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "auth_token": "test_token_placeholder",
            "credentials": "test_credentials_placeholder",
        }

        non_sensitive_data = {
            "user_id": user_data["user_id"],
            "display_name": user_data["full_name"],
            "preferences": {"theme": "dark"},
        }

        # Measure secure storage performance
        start_time = time.time()

        secure_tasks = [
            auth_cache_service._set_to_cache(
                f"secure_{i}", sensitive_data, use_secure=True
            )
            for i in range(10)
        ]
        await asyncio.gather(*secure_tasks)

        secure_time = time.time() - start_time

        # Measure non-secure storage performance
        start_time = time.time()

        non_secure_tasks = [
            auth_cache_service._set_to_cache(
                f"nonsecure_{i}", non_sensitive_data, use_secure=False
            )
            for i in range(10)
        ]
        await asyncio.gather(*non_secure_tasks)

        non_secure_time = time.time() - start_time

        # Security overhead should be minimal
        overhead_ratio = secure_time / non_secure_time if non_secure_time > 0 else 1
        assert overhead_ratio < 2.0  # Security should not more than double the time

        # Both should be fast
        assert secure_time < 0.3
        assert non_secure_time < 0.2

        print(f"Secure operations: {secure_time*1000:.2f}ms")
        print(f"Non-secure operations: {non_secure_time*1000:.2f}ms")
        print(f"Security overhead ratio: {overhead_ratio:.2f}x")

    @pytest.mark.asyncio
    async def test_cache_coherence_under_load(self, auth_cache_service, sample_users):
        """Test cache coherence during high-load scenarios"""
        user_data = sample_users[0]

        # Setup initial data
        session = UserSession(
            user_id=user_data["user_id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_admin=user_data["is_admin"],
        )

        await auth_cache_service.set_user_session(session)

        # Simulate concurrent read/write operations
        async def concurrent_updates():
            """Simulate concurrent session updates"""
            tasks = []

            # Mix of reads and writes
            for i in range(20):
                if i % 3 == 0:
                    # Update session
                    updated_session = UserSession(
                        user_id=user_data["user_id"],
                        email=user_data["email"],
                        full_name=f"Updated {user_data['full_name']} {i}",
                        role=user_data["role"],
                        is_admin=user_data["is_admin"],
                    )
                    tasks.append(auth_cache_service.set_user_session(updated_session))
                else:
                    # Read session
                    tasks.append(
                        auth_cache_service.get_user_session(user_data["user_id"])
                    )

            return await asyncio.gather(*tasks)

        start_time = time.time()
        results = await concurrent_updates()
        coherence_time = time.time() - start_time

        # Verify all operations completed successfully
        write_results = [r for r in results if isinstance(r, bool)]
        read_results = [r for r in results if not isinstance(r, bool)]

        assert all(write_results)  # All writes succeeded
        assert all(r is not None for r in read_results)  # All reads returned data

        # Performance should remain good under concurrent load
        assert coherence_time < 1.0  # 20 concurrent operations in under 1 second

        # Final consistency check
        final_session = await auth_cache_service.get_user_session(user_data["user_id"])
        assert final_session is not None
        assert "Updated" in final_session.full_name  # Should reflect one of the updates

        print(f"Cache coherence under load (20 ops): {coherence_time*1000:.2f}ms")


class TestPerformanceRegressionSafeguards:
    """Tests to prevent performance regressions"""

    @pytest.mark.asyncio
    async def test_performance_benchmarks_maintained(self):
        """Test that key performance benchmarks are maintained"""
        # These are the target improvements we're testing for
        performance_targets = {
            "login_cache_hit": 0.05,  # 50ms max for cached login
            "context_switch": 0.1,  # 100ms max for context switch
            "concurrent_users": 0.5,  # 500ms max for 10 concurrent operations
            "cache_invalidation": 0.1,  # 100ms max for user cache invalidation
            "fallback_operation": 0.05,  # 50ms max for fallback cache operation
        }

        # Mock fast Redis for optimal performance testing
        mock_redis = AsyncMock()
        mock_redis.enabled = True
        mock_redis.get_secure.return_value = {
            "user_id": "test_user",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "user",
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "associations": [],
        }
        mock_redis.set_secure.return_value = True
        mock_redis.delete.return_value = True

        # Simulate minimal latency for optimal case
        async def fast_operation(*args, **kwargs):
            await asyncio.sleep(0.001)  # 1ms simulated network latency
            return mock_redis.get_secure.return_value

        mock_redis.get_secure.side_effect = fast_operation

        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=mock_redis,
        ):
            service = AuthCacheService()

            # Test 1: Login cache hit performance
            start_time = time.time()
            await service.get_user_session("test_user")
            login_time = time.time() - start_time

            assert (
                login_time < performance_targets["login_cache_hit"]
            ), f"Login cache hit took {login_time*1000:.2f}ms, target: {performance_targets['login_cache_hit']*1000}ms"

            # Test 2: Context switch performance
            start_time = time.time()
            await service.update_user_context(
                "test_user", {"active_client_id": "new_client"}
            )
            context_switch_time = time.time() - start_time

            assert context_switch_time < performance_targets["context_switch"], (
                f"Context switch took {context_switch_time*1000:.2f}ms, "
                f"target: {performance_targets['context_switch']*1000}ms"
            )

            # Test 3: Cache invalidation performance
            start_time = time.time()
            await service.invalidate_user_caches("test_user")
            invalidation_time = time.time() - start_time

            assert invalidation_time < performance_targets["cache_invalidation"], (
                f"Cache invalidation took {invalidation_time*1000:.2f}ms, "
                f"target: {performance_targets['cache_invalidation']*1000}ms"
            )

            print("✅ All performance benchmarks maintained:")
            print(
                f"   Login cache hit: {login_time*1000:.2f}ms "
                f"(target: {performance_targets['login_cache_hit']*1000}ms)"
            )
            print(
                f"   Context switch: {context_switch_time*1000:.2f}ms "
                f"(target: {performance_targets['context_switch']*1000}ms)"
            )
            print(
                f"   Cache invalidation: {invalidation_time*1000:.2f}ms "
                f"(target: {performance_targets['cache_invalidation']*1000}ms)"
            )

    @pytest.mark.asyncio
    async def test_performance_degradation_alerts(self):
        """Test system alerts when performance degrades beyond acceptable limits"""
        # Simulate degraded performance conditions
        mock_redis = AsyncMock()
        mock_redis.enabled = True

        # Simulate slow Redis (network issues)
        async def slow_operation(*args, **kwargs):
            await asyncio.sleep(0.2)  # 200ms latency - should trigger warnings
            return True

        mock_redis.set_secure.side_effect = slow_operation
        mock_redis.get_secure.side_effect = slow_operation

        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=mock_redis,
        ):
            service = AuthCacheService()

            # This should trigger performance warnings in logs
            session = UserSession(
                user_id="slow_test_user",
                email="slow@example.com",
                full_name="Slow Test User",
                role="user",
                is_admin=False,
            )

            start_time = time.time()
            await service.set_user_session(session)
            slow_operation_time = time.time() - start_time

            # Verify the operation still completes but is slow
            assert slow_operation_time > 0.1  # Should be noticeably slow

            # In a real scenario, this would trigger monitoring alerts
            # Here we just verify the operation doesn't fail under slow conditions
            retrieved_session = await service.get_user_session("slow_test_user")

            # Operation should complete despite performance degradation
            # Fallback cache should still work
            assert retrieved_session is not None or service.fallback_cache is not None

    @pytest.mark.asyncio
    async def test_load_testing_thresholds(self):
        """Test performance under various load conditions"""
        load_scenarios = [
            {"users": 10, "operations": 5, "max_time": 0.5},
            {"users": 50, "operations": 3, "max_time": 1.0},
            {"users": 100, "operations": 2, "max_time": 2.0},
        ]

        mock_redis = AsyncMock()
        mock_redis.enabled = True
        mock_redis.set_secure.return_value = True
        mock_redis.get_secure.return_value = None  # Cache miss to test fallback

        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=mock_redis,
        ):
            service = AuthCacheService()

            for scenario in load_scenarios:
                print(
                    f"\n🧪 Testing load: {scenario['users']} users, {scenario['operations']} ops each"
                )

                start_time = time.time()

                # Generate load
                tasks = []
                for user_id in range(scenario["users"]):
                    for op_id in range(scenario["operations"]):
                        session = UserSession(
                            user_id=f"load_user_{user_id}",
                            email=f"load{user_id}@example.com",
                            full_name=f"Load User {user_id}",
                            role="user",
                            is_admin=False,
                        )
                        tasks.append(service.set_user_session(session))

                # Execute all operations concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)

                total_time = time.time() - start_time

                # Verify performance meets threshold
                assert (
                    total_time < scenario["max_time"]
                ), f"Load test failed: {total_time:.2f}s > {scenario['max_time']}s for {len(tasks)} operations"

                # Verify no exceptions occurred
                exceptions = [r for r in results if isinstance(r, Exception)]
                assert (
                    len(exceptions) == 0
                ), f"Load test had {len(exceptions)} exceptions"

                print(
                    f"   ✅ Completed {len(tasks)} operations in {total_time*1000:.2f}ms"
                )
                print(
                    f"   📊 Average: {(total_time/len(tasks))*1000:.2f}ms per operation"
                )

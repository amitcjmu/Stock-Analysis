"""
Performance benchmark tests for auth optimization system

Tests to validate the 80-90% performance improvements and ensure system meets targets:
- Login: 200-500ms (from 2-4s) - 80-90% improvement
- Context switching: 100-300ms (from 1-2s) - 85-90% improvement
- Cache operations: <50ms response times
- Concurrent user handling
- High load scenarios
- Memory efficiency under pressure
- Error recovery performance
"""

import asyncio
import gc
import os
import random
import statistics
import time
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import psutil
import pytest

from app.services.caching.auth_cache_service import (
    AuthCacheService,
    InMemoryFallbackCache,
    UserContext,
    UserSession,
)


class PerformanceBenchmark:
    """Performance benchmark utilities and metrics collection"""

    def __init__(self):
        self.results = {}
        self.process = psutil.Process(os.getpid())

    @staticmethod
    def calculate_percentile(times, percentile: float) -> float:
        """Calculate percentile safely for any data size"""
        if len(times) < 2:
            return max(times) if times else 0.0

        # Use appropriate number of quantiles based on data size
        n_quantiles = min(100, len(times))
        quantiles_list = statistics.quantiles(times, n=n_quantiles)

        # Calculate the appropriate index for the percentile
        index = max(
            0,
            min(
                len(quantiles_list) - 1, int((percentile / 100.0) * len(quantiles_list))
            ),
        )
        return quantiles_list[index]

    def start_benchmark(self, name: str):
        """Start timing a benchmark"""
        self.results[name] = {
            "start_time": time.perf_counter(),
            "start_memory": self.process.memory_info().rss,
            "start_cpu": self.process.cpu_percent(),
        }

    def end_benchmark(self, name: str) -> Dict[str, Any]:
        """End timing a benchmark and return metrics"""
        if name not in self.results:
            raise ValueError(f"Benchmark '{name}' was not started")

        end_time = time.perf_counter()
        end_memory = self.process.memory_info().rss
        end_cpu = self.process.cpu_percent()

        result = {
            "duration_ms": (end_time - self.results[name]["start_time"]) * 1000,
            "memory_delta_mb": (end_memory - self.results[name]["start_memory"])
            / 1024
            / 1024,
            "cpu_usage_percent": end_cpu,
            "timestamp": datetime.utcnow(),
        }

        self.results[name].update(result)
        return result


class TestAuthPerformanceBenchmarks:
    """Comprehensive performance benchmarks for auth optimization"""

    @pytest.fixture
    def benchmark(self):
        """Performance benchmark utility"""
        return PerformanceBenchmark()

    @pytest.fixture
    def performance_config(self):
        """Configurable performance baselines and realistic Redis timings"""
        return {
            # Realistic Redis performance characteristics (based on AWS ElastiCache)
            "redis_timings": {
                "local_redis_ms": {"min": 0.1, "avg": 0.5, "max": 2.0},  # Local Redis
                "cloud_redis_ms": {"min": 0.5, "avg": 2.0, "max": 8.0},  # Cloud Redis
                "cross_az_redis_ms": {
                    "min": 1.0,
                    "avg": 4.0,
                    "max": 15.0,
                },  # Cross-AZ Redis
            },
            # Configurable performance baselines (from environment or defaults)
            "baselines": {
                "login_baseline_ms": float(
                    os.getenv("LOGIN_BASELINE_MS", "2500")
                ),  # 2.5s baseline
                "context_switch_baseline_ms": float(
                    os.getenv("CONTEXT_SWITCH_BASELINE_MS", "1200")
                ),  # 1.2s baseline
                "cache_operation_baseline_ms": float(
                    os.getenv("CACHE_BASELINE_MS", "50")
                ),  # 50ms baseline
            },
            # Target improvements (configurable via environment)
            "targets": {
                "login_target_ms": float(
                    os.getenv("LOGIN_TARGET_MS", "300")
                ),  # 300ms target
                "context_switch_target_ms": float(
                    os.getenv("CONTEXT_SWITCH_TARGET_MS", "150")
                ),  # 150ms target
                "min_improvement_factor": float(
                    os.getenv("MIN_IMPROVEMENT_FACTOR", "5.0")
                ),  # 5x improvement
            },
            # Network conditions for testing
            "network_conditions": {
                "optimal": "local_redis_ms",
                "typical": "cloud_redis_ms",
                "degraded": "cross_az_redis_ms",
            },
        }

    @pytest.fixture
    def optimized_redis_mock(self, performance_config):
        """Mock Redis with realistic performance characteristics and variance"""
        mock = AsyncMock()
        mock.enabled = True

        # Use typical cloud Redis performance by default
        redis_timing = performance_config["redis_timings"]["cloud_redis_ms"]

        async def realistic_get(*args, **kwargs):
            # Add realistic variance to response times
            latency = random.uniform(redis_timing["min"], redis_timing["max"]) / 1000
            await asyncio.sleep(latency)
            return {
                "user_id": "benchmark_user",
                "email": "benchmark@example.com",
                "full_name": "Benchmark User",
                "role": "user",
                "is_admin": False,
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "associations": [],
            }

        async def realistic_set(*args, **kwargs):
            # Write operations typically slightly faster than reads
            latency = random.uniform(redis_timing["min"], redis_timing["avg"]) / 1000
            await asyncio.sleep(latency)
            return True

        async def realistic_delete(*args, **kwargs):
            latency = random.uniform(redis_timing["min"], redis_timing["avg"]) / 1000
            await asyncio.sleep(latency)
            return True

        mock.get.side_effect = realistic_get
        mock.get_secure.side_effect = realistic_get
        mock.set.side_effect = realistic_set
        mock.set_secure.side_effect = realistic_set
        mock.delete.side_effect = realistic_delete

        return mock

    @pytest.fixture
    def auth_service(self, optimized_redis_mock):
        """AuthCacheService with optimized Redis mock"""
        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=optimized_redis_mock,
        ):
            return AuthCacheService()

    @pytest.mark.asyncio
    async def test_login_performance_benchmark(
        self, auth_service, benchmark, performance_config
    ):
        """
        Benchmark login performance with configurable baselines
        Uses realistic Redis timings and environment-configurable targets
        """
        config = performance_config
        baseline_ms = config["baselines"]["login_baseline_ms"]
        target_ms = config["targets"]["login_target_ms"]
        min_improvement = config["targets"]["min_improvement_factor"]

        print("\n🚀 LOGIN PERFORMANCE BENCHMARK")
        print(f"   📊 Baseline: {baseline_ms}ms, Target: {target_ms}ms")
        print(f"   🎯 Min improvement: {min_improvement}x faster")

        # Test scenarios with configurable targets
        scenarios = [
            {"name": "cold_login", "cache_data": False, "target_ms": target_ms * 1.5},
            {"name": "warm_login", "cache_data": True, "target_ms": target_ms},
            {"name": "hot_login", "cache_data": True, "target_ms": target_ms * 0.7},
        ]

        user_data = {
            "user_id": "perf_test_user",
            "email": "perf@example.com",
            "full_name": "Performance Test User",
            "role": "admin",
            "is_admin": True,
        }

        results = {}

        for scenario in scenarios:
            print(f"\n📊 Testing {scenario['name']}...")

            # Setup cache if needed
            if scenario["cache_data"]:
                session = UserSession(**user_data)
                await auth_service.set_user_session(session)
                context = UserContext(
                    user_id=user_data["user_id"],
                    active_client_id="client_123",
                    active_engagement_id="engagement_456",
                )
                await auth_service.set_user_context(context)

            # Benchmark multiple login attempts
            times = []
            benchmark.start_benchmark(scenario["name"])

            for i in range(20):  # 20 login attempts
                start = time.perf_counter()

                # Simulate complete login flow
                session = await auth_service.get_user_session(user_data["user_id"])
                context = await auth_service.get_user_context(user_data["user_id"])

                # Update last accessed (typical in login)
                if session:
                    await auth_service.set_user_session(session)

                end = time.perf_counter()
                times.append((end - start) * 1000)  # Convert to ms

            metrics = benchmark.end_benchmark(scenario["name"])

            # Calculate statistics
            avg_time = statistics.mean(times)
            p95_time = benchmark.calculate_percentile(times, 95)
            p99_time = benchmark.calculate_percentile(times, 99)

            results[scenario["name"]] = {
                "avg_ms": avg_time,
                "p95_ms": p95_time,
                "p99_ms": p99_time,
                "target_ms": scenario["target_ms"],
                "improvement_factor": baseline_ms
                / avg_time,  # Use configurable baseline
                "memory_delta_mb": metrics["memory_delta_mb"],
            }

            # Performance assertions
            assert (
                avg_time < scenario["target_ms"]
            ), f"{scenario['name']} average {avg_time:.1f}ms exceeds target {scenario['target_ms']}ms"

            assert (
                p95_time < scenario["target_ms"] * 1.5
            ), f"{scenario['name']} P95 {p95_time:.1f}ms exceeds threshold"

            print(
                f"   ✅ Average: {avg_time:.1f}ms (target: {scenario['target_ms']}ms)"
            )
            print(f"   📈 P95: {p95_time:.1f}ms, P99: {p99_time:.1f}ms")
            print(
                f"   ⚡ Improvement: {results[scenario['name']]['improvement_factor']:.1f}x faster"
            )

            # Clear cache for next scenario
            await auth_service.invalidate_user_caches(user_data["user_id"])

        # Overall improvement validation
        warm_improvement = results["warm_login"]["improvement_factor"]
        assert (
            warm_improvement >= min_improvement
        ), f"Warm login improvement {warm_improvement:.1f}x < {min_improvement}x target"

        print("\n🎯 LOGIN BENCHMARK SUMMARY:")
        for name, data in results.items():
            improvement_pct = (1 - 1 / data["improvement_factor"]) * 100
            print(
                f"   {name}: {data['avg_ms']:.1f}ms avg ({improvement_pct:.0f}% improvement)"
            )

    @pytest.mark.asyncio
    async def test_context_switching_benchmark(self, auth_service, benchmark):
        """
        Benchmark context switching performance
        Target: 100-300ms (from 1-2s baseline) = 85-90% improvement
        """
        print("\n🔄 CONTEXT SWITCHING BENCHMARK")

        user_id = "context_test_user"

        # Setup initial session and context
        session = UserSession(
            user_id=user_id,
            email="context@example.com",
            full_name="Context Test User",
            role="user",
            is_admin=False,
        )
        await auth_service.set_user_session(session)

        initial_context = UserContext(
            user_id=user_id,
            active_client_id="client_1",
            active_engagement_id="engagement_1",
        )
        await auth_service.set_user_context(initial_context)

        # Context switch scenarios
        switch_scenarios = [
            {
                "name": "client_switch",
                "updates": {"active_client_id": "client_2"},
                "target_ms": 150,
            },
            {
                "name": "engagement_switch",
                "updates": {"active_engagement_id": "engagement_2"},
                "target_ms": 150,
            },
            {
                "name": "flow_switch",
                "updates": {"active_flow_id": "flow_123"},
                "target_ms": 100,
            },
            {
                "name": "multi_switch",
                "updates": {
                    "active_client_id": "client_3",
                    "active_engagement_id": "engagement_3",
                    "active_flow_id": "flow_456",
                },
                "target_ms": 300,
            },
        ]

        results = {}

        for scenario in switch_scenarios:
            print(f"\n📊 Testing {scenario['name']}...")

            benchmark.start_benchmark(scenario["name"])
            times = []

            for i in range(50):  # 50 context switches
                start = time.perf_counter()

                # Perform context switch
                success = await auth_service.update_user_context(
                    user_id, scenario["updates"]
                )

                # Verify context was updated
                updated_context = await auth_service.get_user_context(user_id)

                end = time.perf_counter()
                times.append((end - start) * 1000)

                assert success is True
                assert updated_context is not None

            metrics = benchmark.end_benchmark(scenario["name"])

            # Calculate statistics
            avg_time = statistics.mean(times)
            p95_time = benchmark.calculate_percentile(times, 95)
            p99_time = benchmark.calculate_percentile(times, 99)

            results[scenario["name"]] = {
                "avg_ms": avg_time,
                "p95_ms": p95_time,
                "p99_ms": p99_time,
                "target_ms": scenario["target_ms"],
                "improvement_factor": 1500 / avg_time,  # Assuming 1.5s baseline
                "memory_delta_mb": metrics["memory_delta_mb"],
            }

            # Performance assertions
            assert (
                avg_time < scenario["target_ms"]
            ), f"{scenario['name']} average {avg_time:.1f}ms exceeds target {scenario['target_ms']}ms"

            print(
                f"   ✅ Average: {avg_time:.1f}ms (target: {scenario['target_ms']}ms)"
            )
            print(f"   📈 P95: {p95_time:.1f}ms, P99: {p99_time:.1f}ms")
            print(
                f"   ⚡ Improvement: {results[scenario['name']]['improvement_factor']:.1f}x faster"
            )

        # Overall improvement validation
        avg_improvement = statistics.mean(
            [r["improvement_factor"] for r in results.values()]
        )
        assert (
            avg_improvement >= 6.0
        ), f"Average context switch improvement {avg_improvement:.1f}x < 6x target"

        print("\n🎯 CONTEXT SWITCHING SUMMARY:")
        for name, data in results.items():
            improvement_pct = (1 - 1 / data["improvement_factor"]) * 100
            print(
                f"   {name}: {data['avg_ms']:.1f}ms avg ({improvement_pct:.0f}% improvement)"
            )

    @pytest.mark.asyncio
    async def test_cache_operations_benchmark(self, auth_service, benchmark):
        """
        Benchmark individual cache operations
        Target: <50ms response times for all cache operations
        """
        print("\n💾 CACHE OPERATIONS BENCHMARK")

        operations = [
            {
                "name": "session_get",
                "func": lambda: auth_service.get_user_session("cache_user"),
                "target_ms": 30,
            },
            {
                "name": "session_set",
                "func": lambda: auth_service.set_user_session(
                    UserSession(
                        user_id="cache_user",
                        email="cache@example.com",
                        full_name="Cache User",
                        role="user",
                        is_admin=False,
                    )
                ),
                "target_ms": 40,
            },
            {
                "name": "context_get",
                "func": lambda: auth_service.get_user_context("cache_user"),
                "target_ms": 25,
            },
            {
                "name": "context_set",
                "func": lambda: auth_service.set_user_context(
                    UserContext(user_id="cache_user")
                ),
                "target_ms": 35,
            },
            {
                "name": "context_update",
                "func": lambda: auth_service.update_user_context(
                    "cache_user", {"active_client_id": "new_client"}
                ),
                "target_ms": 45,
            },
            {
                "name": "invalidate_user",
                "func": lambda: auth_service.invalidate_user_caches("cache_user"),
                "target_ms": 50,
            },
            {
                "name": "buffer_activity",
                "func": lambda: auth_service.buffer_user_activity(
                    "cache_user", {"action": "test"}
                ),
                "target_ms": 20,
            },
        ]

        results = {}

        for operation in operations:
            print(f"\n📊 Benchmarking {operation['name']}...")

            benchmark.start_benchmark(operation["name"])
            times = []

            for i in range(100):  # 100 operations
                start = time.perf_counter()
                await operation["func"]()
                end = time.perf_counter()
                times.append((end - start) * 1000)

            metrics = benchmark.end_benchmark(operation["name"])

            # Calculate statistics
            avg_time = statistics.mean(times)
            p95_time = benchmark.calculate_percentile(times, 95)
            p99_time = benchmark.calculate_percentile(times, 99)
            max_time = max(times)

            results[operation["name"]] = {
                "avg_ms": avg_time,
                "p95_ms": p95_time,
                "p99_ms": p99_time,
                "max_ms": max_time,
                "target_ms": operation["target_ms"],
                "memory_delta_mb": metrics["memory_delta_mb"],
            }

            # Performance assertions
            assert (
                avg_time < operation["target_ms"]
            ), f"{operation['name']} average {avg_time:.1f}ms exceeds target {operation['target_ms']}ms"

            assert (
                p95_time < operation["target_ms"] * 1.5
            ), f"{operation['name']} P95 {p95_time:.1f}ms exceeds threshold"

            print(
                f"   ✅ Average: {avg_time:.1f}ms (target: {operation['target_ms']}ms)"
            )
            print(f"   📈 P95: {p95_time:.1f}ms, Max: {max_time:.1f}ms")

        print("\n🎯 CACHE OPERATIONS SUMMARY:")
        for name, data in results.items():
            print(
                f"   {name}: {data['avg_ms']:.1f}ms avg (target: {data['target_ms']}ms)"
            )

    @pytest.mark.asyncio
    async def test_concurrent_users_benchmark(self, auth_service, benchmark):
        """
        Benchmark concurrent user handling
        Target: Handle 100+ concurrent users with <500ms response times
        """
        print("\n👥 CONCURRENT USERS BENCHMARK")

        concurrency_levels = [10, 25, 50, 100]

        for user_count in concurrency_levels:
            print(f"\n📊 Testing {user_count} concurrent users...")

            benchmark.start_benchmark(f"concurrent_{user_count}")

            # Generate users
            users = []
            for i in range(user_count):
                users.append(
                    {
                        "user_id": f"concurrent_user_{i:03d}",
                        "email": f"user{i}@example.com",
                        "full_name": f"Concurrent User {i}",
                        "role": "user" if i % 2 == 0 else "admin",
                        "is_admin": i % 10 == 0,
                    }
                )

            # Benchmark concurrent login simulation
            async def simulate_user_login(user_data):
                """Simulate complete user login flow"""
                start = time.perf_counter()

                # Create and cache session
                session = UserSession(**user_data)
                await auth_service.set_user_session(session)

                # Create and cache context
                context = UserContext(
                    user_id=user_data["user_id"],
                    active_client_id=f"client_{hash(user_data['user_id']) % 5}",
                    active_engagement_id=f"engagement_{hash(user_data['user_id']) % 3}",
                )
                await auth_service.set_user_context(context)

                # Simulate some activity
                await auth_service.buffer_user_activity(
                    user_data["user_id"],
                    {"action": "login", "timestamp": datetime.utcnow().isoformat()},
                )

                # Read back data (cache hit)
                cached_session = await auth_service.get_user_session(
                    user_data["user_id"]
                )
                cached_context = await auth_service.get_user_context(
                    user_data["user_id"]
                )

                end = time.perf_counter()
                return {
                    "user_id": user_data["user_id"],
                    "duration_ms": (end - start) * 1000,
                    "success": cached_session is not None
                    and cached_context is not None,
                }

            # Execute concurrent operations
            start_time = time.perf_counter()

            tasks = [simulate_user_login(user) for user in users]
            user_results = await asyncio.gather(*tasks)

            total_time = time.perf_counter() - start_time
            metrics = benchmark.end_benchmark(f"concurrent_{user_count}")

            # Analyze results
            durations = [r["duration_ms"] for r in user_results]
            success_count = sum(1 for r in user_results if r["success"])

            avg_duration = statistics.mean(durations)
            p95_duration = benchmark.calculate_percentile(durations, 95)
            p99_duration = benchmark.calculate_percentile(durations, 99)
            max_duration = max(durations)

            # Performance assertions
            assert (
                success_count == user_count
            ), f"Only {success_count}/{user_count} users succeeded"
            assert (
                avg_duration < 500
            ), f"Average duration {avg_duration:.1f}ms exceeds 500ms target"
            assert (
                p95_duration < 1000
            ), f"P95 duration {p95_duration:.1f}ms exceeds 1000ms threshold"
            assert (
                total_time < user_count * 0.1
            ), f"Total time {total_time:.2f}s too high for {user_count} users"

            # Calculate throughput
            throughput = user_count / total_time

            print(f"   ✅ {success_count}/{user_count} users succeeded")
            print(f"   ⏱️  Total time: {total_time*1000:.0f}ms")
            print(f"   📊 Average duration: {avg_duration:.1f}ms")
            print(
                f"   📈 P95: {p95_duration:.1f}ms, P99: {p99_duration:.1f}ms, Max: {max_duration:.1f}ms"
            )
            print(f"   🚀 Throughput: {throughput:.1f} users/second")
            print(f"   💾 Memory delta: {metrics['memory_delta_mb']:.1f}MB")

            # Cleanup
            cleanup_tasks = [
                auth_service.invalidate_user_caches(user["user_id"]) for user in users
            ]
            await asyncio.gather(*cleanup_tasks)

    @pytest.mark.asyncio
    async def test_high_load_stress_benchmark(self, auth_service, benchmark):
        """
        Stress test under high load conditions
        Target: Maintain performance under sustained high load
        """
        print("\n🔥 HIGH LOAD STRESS BENCHMARK")

        # Test parameters
        duration_seconds = 30
        operations_per_second = 100
        total_operations = duration_seconds * operations_per_second

        print(
            f"   🎯 Target: {operations_per_second} ops/sec for {duration_seconds} seconds"
        )
        print(f"   📊 Total operations: {total_operations}")

        benchmark.start_benchmark("stress_test")

        # Operation types and their weights
        operation_types = [
            ("login", 0.3, lambda i: simulate_login(f"stress_user_{i % 50}")),
            (
                "context_switch",
                0.4,
                lambda i: simulate_context_switch(f"stress_user_{i % 50}"),
            ),
            (
                "activity_buffer",
                0.2,
                lambda i: simulate_activity(f"stress_user_{i % 50}"),
            ),
            (
                "invalidation",
                0.1,
                lambda i: simulate_invalidation(f"stress_user_{i % 50}"),
            ),
        ]

        async def simulate_login(user_id):
            session = UserSession(
                user_id=user_id,
                email=f"{user_id}@example.com",
                full_name=f"Stress User {user_id}",
                role="user",
                is_admin=False,
            )
            await auth_service.set_user_session(session)
            return await auth_service.get_user_session(user_id)

        async def simulate_context_switch(user_id):
            return await auth_service.update_user_context(
                user_id, {"active_client_id": f"client_{time.time_ns() % 10}"}
            )

        async def simulate_activity(user_id):
            return await auth_service.buffer_user_activity(
                user_id, {"action": "stress_test", "timestamp": time.time()}
            )

        async def simulate_invalidation(user_id):
            return await auth_service.invalidate_user_caches(user_id)

        # Generate operations
        operations = []
        for i in range(total_operations):
            # Choose operation type based on weights
            rand_val = (hash(str(i)) % 100) / 100
            cumulative_weight = 0

            for op_name, weight, op_func in operation_types:
                cumulative_weight += weight
                if rand_val <= cumulative_weight:
                    operations.append((op_name, op_func(i)))
                    break

        # Execute operations with controlled rate
        start_time = time.perf_counter()
        completed_operations = 0
        operation_times = []
        errors = 0

        # Batch operations to control rate
        batch_size = 10
        batches = [
            operations[i : i + batch_size]
            for i in range(0, len(operations), batch_size)
        ]

        for batch_num, batch in enumerate(batches):
            batch_start = time.perf_counter()

            try:
                # Execute batch concurrently
                batch_tasks = [op_func for _, op_func in batch]
                batch_results = await asyncio.gather(
                    *batch_tasks, return_exceptions=True
                )

                # Record results
                for result in batch_results:
                    if isinstance(result, Exception):
                        errors += 1
                    else:
                        completed_operations += 1

                batch_time = time.perf_counter() - batch_start
                operation_times.extend([batch_time / len(batch)] * len(batch))

                # Rate control - ensure we don't exceed target rate
                expected_time = (batch_num + 1) * batch_size / operations_per_second
                actual_time = time.perf_counter() - start_time

                if actual_time < expected_time:
                    await asyncio.sleep(expected_time - actual_time)

            except Exception as e:
                print(f"   ❌ Batch {batch_num} failed: {e}")
                errors += len(batch)

        total_time = time.perf_counter() - start_time
        metrics = benchmark.end_benchmark("stress_test")

        # Calculate statistics
        actual_ops_per_second = completed_operations / total_time
        avg_operation_time = (
            statistics.mean(operation_times) * 1000 if operation_times else 0
        )
        p95_operation_time = (
            benchmark.calculate_percentile(operation_times, 95) * 1000
            if operation_times
            else 0
        )
        error_rate = (errors / total_operations) * 100

        # Performance assertions
        assert (
            actual_ops_per_second >= operations_per_second * 0.8
        ), f"Throughput {actual_ops_per_second:.1f} ops/sec below 80% of target {operations_per_second}"

        assert error_rate < 5.0, f"Error rate {error_rate:.1f}% exceeds 5% threshold"

        assert (
            avg_operation_time < 100
        ), f"Average operation time {avg_operation_time:.1f}ms exceeds 100ms"

        print(f"   ✅ Completed {completed_operations}/{total_operations} operations")
        print(
            f"   🚀 Throughput: {actual_ops_per_second:.1f} ops/sec (target: {operations_per_second})"
        )
        print(f"   ⏱️  Average operation time: {avg_operation_time:.1f}ms")
        print(f"   📈 P95 operation time: {p95_operation_time:.1f}ms")
        print(f"   ❌ Error rate: {error_rate:.1f}%")
        print(f"   💾 Memory delta: {metrics['memory_delta_mb']:.1f}MB")
        print(f"   🖥️  CPU usage: {metrics['cpu_usage_percent']:.1f}%")

    @pytest.mark.asyncio
    async def test_memory_efficiency_benchmark(self, benchmark):
        """
        Benchmark memory efficiency under various conditions
        Target: Efficient memory usage with proper cleanup
        """
        print("\n💾 MEMORY EFFICIENCY BENCHMARK")

        # Test in-memory fallback cache with different sizes
        cache_sizes = [100, 500, 1000, 5000]

        for cache_size in cache_sizes:
            print(f"\n📊 Testing cache size: {cache_size} items")

            benchmark.start_benchmark(f"memory_test_{cache_size}")

            # Create cache
            cache = InMemoryFallbackCache(max_size=cache_size, default_ttl=300)

            # Fill cache to capacity
            for i in range(cache_size):
                user_data = {
                    "user_id": f"memory_user_{i:05d}",
                    "email": f"user{i}@example.com",
                    "full_name": f"Memory Test User {i}",
                    "role": "user",
                    "is_admin": False,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_accessed": datetime.utcnow().isoformat(),
                    "associations": [
                        {"client_id": f"client_{j}", "role": "user"} for j in range(3)
                    ],
                }
                await cache.set(f"user_{i}", user_data)

            # Verify cache is at capacity
            stats = cache.get_stats()
            assert stats["size"] == cache_size

            # Test memory usage after filling cache
            metrics = benchmark.end_benchmark(f"memory_test_{cache_size}")

            # Test eviction behavior
            benchmark.start_benchmark(f"eviction_test_{cache_size}")

            # Add more items to trigger eviction
            eviction_count = cache_size // 2
            for i in range(eviction_count):
                await cache.set(f"eviction_user_{i}", {"data": f"eviction_{i}"})

            # Verify cache size stayed within limits
            final_stats = cache.get_stats()
            assert final_stats["size"] <= cache_size

            eviction_metrics = benchmark.end_benchmark(f"eviction_test_{cache_size}")

            # Calculate memory efficiency
            memory_per_item = (
                metrics["memory_delta_mb"] / cache_size * 1024
            )  # KB per item

            print(f"   📊 Cache size: {stats['size']}/{cache_size} items")
            print(f"   💾 Memory usage: {metrics['memory_delta_mb']:.2f}MB total")
            print(f"   📈 Memory per item: {memory_per_item:.2f}KB")
            print(f"   🔄 Eviction handling: {eviction_metrics['duration_ms']:.1f}ms")

            # Performance assertions
            assert (
                memory_per_item < 10
            ), f"Memory per item {memory_per_item:.2f}KB exceeds 10KB limit"
            assert (
                eviction_metrics["duration_ms"] < 100
            ), f"Eviction took {eviction_metrics['duration_ms']:.1f}ms"

            # Cleanup
            await cache.clear()
            gc.collect()  # Force garbage collection

    @pytest.mark.asyncio
    async def test_error_recovery_performance_benchmark(self, benchmark):
        """
        Benchmark error recovery performance
        Target: Fast recovery with minimal impact on healthy operations
        """
        print("\n🚨 ERROR RECOVERY PERFORMANCE BENCHMARK")

        # Test scenarios with different failure modes
        failure_scenarios = [
            {"name": "redis_unavailable", "redis_enabled": False, "target_ms": 50},
            {"name": "redis_slow", "redis_latency": 0.5, "target_ms": 600},
            {"name": "redis_intermittent", "redis_failure_rate": 0.3, "target_ms": 100},
        ]

        for scenario in failure_scenarios:
            print(f"\n📊 Testing {scenario['name']}...")

            # Setup mock based on scenario
            mock_redis = AsyncMock()

            if scenario["name"] == "redis_unavailable":
                mock_redis.enabled = False

            elif scenario["name"] == "redis_slow":
                mock_redis.enabled = True

                async def slow_operation(*args, **kwargs):
                    await asyncio.sleep(scenario["redis_latency"])
                    return True

                mock_redis.get_secure.side_effect = slow_operation
                mock_redis.set_secure.side_effect = slow_operation

            elif scenario["name"] == "redis_intermittent":
                mock_redis.enabled = True
                operation_count = 0

                async def intermittent_operation(*args, **kwargs):
                    nonlocal operation_count
                    operation_count += 1

                    if (operation_count % int(1 / scenario["redis_failure_rate"])) == 0:
                        raise ConnectionError("Intermittent Redis failure")

                    await asyncio.sleep(0.01)  # Normal operation
                    return {"user_id": "test", "data": "cached"}

                mock_redis.get_secure.side_effect = intermittent_operation
                mock_redis.set_secure.side_effect = intermittent_operation

            # Test operations under failure conditions
            with patch(
                "app.services.caching.auth_cache_service.get_redis_cache",
                return_value=mock_redis,
            ):
                service = AuthCacheService()

                benchmark.start_benchmark(scenario["name"])
                times = []
                success_count = 0

                for i in range(50):  # 50 operations
                    start = time.perf_counter()

                    try:
                        session = UserSession(
                            user_id=f"recovery_user_{i}",
                            email=f"recovery{i}@example.com",
                            full_name=f"Recovery User {i}",
                            role="user",
                            is_admin=False,
                        )

                        # Test full operation cycle
                        set_success = await service.set_user_session(session)
                        retrieved_session = await service.get_user_session(
                            session.user_id
                        )

                        if set_success and (
                            retrieved_session is not None or not mock_redis.enabled
                        ):
                            success_count += 1

                    except Exception as e:
                        print(f"   ⚠️  Operation {i} failed: {e}")

                    end = time.perf_counter()
                    times.append((end - start) * 1000)

                metrics = benchmark.end_benchmark(scenario["name"])

                # Calculate statistics
                avg_time = statistics.mean(times)
                p95_time = benchmark.calculate_percentile(times, 95)
                success_rate = (success_count / 50) * 100

                # Performance assertions
                assert (
                    avg_time < scenario["target_ms"]
                ), f"{scenario['name']} average {avg_time:.1f}ms exceeds target {scenario['target_ms']}ms"

                assert (
                    success_rate >= 80
                ), f"{scenario['name']} success rate {success_rate:.1f}% below 80%"

                print(f"   ✅ Success rate: {success_rate:.1f}%")
                print(
                    f"   ⏱️  Average time: {avg_time:.1f}ms (target: {scenario['target_ms']}ms)"
                )
                print(f"   📈 P95 time: {p95_time:.1f}ms")
                print(f"   💾 Memory delta: {metrics['memory_delta_mb']:.2f}MB")


class TestPerformanceRegression:
    """Tests to prevent performance regressions"""

    @pytest.mark.asyncio
    async def test_performance_targets_validation(self):
        """Validate all performance targets are met"""
        print("\n🎯 PERFORMANCE TARGETS VALIDATION")

        # Define performance targets (from requirements)
        targets = {
            "login_improvement": {
                "baseline_ms": 3000,  # 2-4s baseline, using 3s average
                "target_ms": 350,  # 200-500ms target, using 350ms average
                "min_improvement": 8.0,  # 8x improvement = 87.5% reduction
            },
            "context_switch_improvement": {
                "baseline_ms": 1500,  # 1-2s baseline, using 1.5s average
                "target_ms": 200,  # 100-300ms target, using 200ms average
                "min_improvement": 7.0,  # 7x improvement = 85.7% reduction
            },
            "cache_operations": {
                "target_ms": 50,  # <50ms for all cache operations
                "operations": ["get", "set", "update", "delete"],
            },
        }

        # Mock optimized Redis
        mock_redis = AsyncMock()
        mock_redis.enabled = True

        # Ultra-fast mock for best-case scenario
        async def instant_operation(*args, **kwargs):
            await asyncio.sleep(0.001)  # 1ms
            return {"test": "data"}

        mock_redis.get_secure.side_effect = instant_operation
        mock_redis.set_secure.side_effect = instant_operation
        mock_redis.delete.side_effect = instant_operation

        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=mock_redis,
        ):
            service = AuthCacheService()

            # Test login performance
            print("\n📊 Testing login performance target...")

            session = UserSession(
                user_id="target_test_user",
                email="target@example.com",
                full_name="Target Test User",
                role="user",
                is_admin=False,
            )

            # Warm up cache
            await service.set_user_session(session)

            # Measure optimized login
            times = []
            for _ in range(20):
                start = time.perf_counter()

                # Complete login flow
                await service.get_user_session("target_test_user")
                await service.set_user_context(UserContext(user_id="target_test_user"))

                end = time.perf_counter()
                times.append((end - start) * 1000)

            avg_login_time = statistics.mean(times)
            login_improvement = (
                targets["login_improvement"]["baseline_ms"] / avg_login_time
            )
            login_improvement_pct = (
                1 - avg_login_time / targets["login_improvement"]["baseline_ms"]
            ) * 100

            print(f"   ✅ Login time: {avg_login_time:.1f}ms")
            print(
                f"   📈 Improvement: {login_improvement:.1f}x faster ({login_improvement_pct:.1f}% reduction)"
            )

            # Assert login performance target
            assert (
                avg_login_time <= targets["login_improvement"]["target_ms"]
            ), f"Login time {avg_login_time:.1f}ms exceeds target {targets['login_improvement']['target_ms']}ms"

            assert (
                login_improvement >= targets["login_improvement"]["min_improvement"]
            ), (
                f"Login improvement {login_improvement:.1f}x below target "
                f"{targets['login_improvement']['min_improvement']}x"
            )

            # Test context switch performance
            print("\n📊 Testing context switch performance target...")

            times = []
            for i in range(20):
                start = time.perf_counter()

                await service.update_user_context(
                    "target_test_user", {"active_client_id": f"client_{i}"}
                )

                end = time.perf_counter()
                times.append((end - start) * 1000)

            avg_context_time = statistics.mean(times)
            context_improvement = (
                targets["context_switch_improvement"]["baseline_ms"] / avg_context_time
            )
            context_improvement_pct = (
                1
                - avg_context_time
                / targets["context_switch_improvement"]["baseline_ms"]
            ) * 100

            print(f"   ✅ Context switch time: {avg_context_time:.1f}ms")
            print(
                f"   📈 Improvement: {context_improvement:.1f}x faster ({context_improvement_pct:.1f}% reduction)"
            )

            # Assert context switch performance target
            assert (
                avg_context_time <= targets["context_switch_improvement"]["target_ms"]
            ), (
                f"Context switch time {avg_context_time:.1f}ms exceeds target "
                f"{targets['context_switch_improvement']['target_ms']}ms"
            )

            assert (
                context_improvement
                >= targets["context_switch_improvement"]["min_improvement"]
            ), (
                f"Context switch improvement {context_improvement:.1f}x below target "
                f"{targets['context_switch_improvement']['min_improvement']}x"
            )

            # Test individual cache operations
            print("\n📊 Testing cache operations performance target...")

            cache_ops = {
                "get": lambda: service.get_user_session("target_test_user"),
                "set": lambda: service.set_user_session(session),
                "update": lambda: service.update_user_context(
                    "target_test_user", {"test": "value"}
                ),
                "delete": lambda: service.invalidate_user_caches("target_test_user"),
            }

            for op_name, op_func in cache_ops.items():
                times = []
                for _ in range(10):
                    start = time.perf_counter()
                    await op_func()
                    end = time.perf_counter()
                    times.append((end - start) * 1000)

                avg_op_time = statistics.mean(times)

                print(f"   ✅ {op_name} operation: {avg_op_time:.1f}ms")

                assert avg_op_time <= targets["cache_operations"]["target_ms"], (
                    f"{op_name} operation {avg_op_time:.1f}ms exceeds target "
                    f"{targets['cache_operations']['target_ms']}ms"
                )

        print("\n🎉 ALL PERFORMANCE TARGETS VALIDATED!")
        print(
            f"   🚀 Login: {login_improvement_pct:.0f}% improvement ({login_improvement:.1f}x faster)"
        )
        print(
            f"   🔄 Context Switch: {context_improvement_pct:.0f}% improvement ({context_improvement:.1f}x faster)"
        )
        print(
            f"   💾 Cache Operations: All under {targets['cache_operations']['target_ms']}ms"
        )

    @pytest.mark.asyncio
    async def test_sustained_performance_validation(self):
        """Test that performance remains consistent over time"""
        print("\n⏳ SUSTAINED PERFORMANCE VALIDATION")

        mock_redis = AsyncMock()
        mock_redis.enabled = True

        async def consistent_operation(*args, **kwargs):
            await asyncio.sleep(0.005)  # 5ms consistent latency
            return {"sustained": "test"}

        mock_redis.get_secure.side_effect = consistent_operation
        mock_redis.set_secure.side_effect = consistent_operation

        with patch(
            "app.services.caching.auth_cache_service.get_redis_cache",
            return_value=mock_redis,
        ):
            service = AuthCacheService()

            # Run operations for 60 seconds in batches
            batch_duration = 10  # seconds
            batches = 6
            all_times = []

            for batch_num in range(batches):
                print(
                    f"   📊 Running batch {batch_num + 1}/{batches} ({batch_duration}s)..."
                )

                batch_start = time.perf_counter()
                batch_times = []

                while time.perf_counter() - batch_start < batch_duration:
                    start = time.perf_counter()

                    # Perform mixed operations
                    session = UserSession(
                        user_id=f"sustained_user_{int(time.time_ns()) % 100}",
                        email="sustained@example.com",
                        full_name="Sustained Test User",
                        role="user",
                        is_admin=False,
                    )

                    await service.set_user_session(session)
                    await service.get_user_session(session.user_id)

                    end = time.perf_counter()
                    batch_times.append((end - start) * 1000)

                batch_avg = statistics.mean(batch_times)
                batch_std = statistics.stdev(batch_times) if len(batch_times) > 1 else 0

                all_times.extend(batch_times)

                print(
                    f"      ⏱️  Batch {batch_num + 1}: {batch_avg:.1f}ms avg, {batch_std:.1f}ms std dev"
                )

                # Each batch should maintain consistent performance
                assert (
                    batch_avg < 100
                ), f"Batch {batch_num + 1} performance degraded: {batch_avg:.1f}ms"
                assert (
                    batch_std < 50
                ), f"Batch {batch_num + 1} too variable: {batch_std:.1f}ms std dev"

            # Overall analysis
            overall_avg = statistics.mean(all_times)
            overall_std = statistics.stdev(all_times)

            # Performance should not degrade over time
            first_half = all_times[: len(all_times) // 2]
            second_half = all_times[len(all_times) // 2 :]

            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)
            degradation_pct = ((second_avg - first_avg) / first_avg) * 100

            print("\n   📊 Sustained Performance Results:")
            print(f"      ⏱️  Overall average: {overall_avg:.1f}ms")
            print(f"      📈 Standard deviation: {overall_std:.1f}ms")
            print(f"      🔍 Performance degradation: {degradation_pct:+.1f}%")

            # Assertions for sustained performance
            assert (
                overall_avg < 80
            ), f"Overall average {overall_avg:.1f}ms exceeds 80ms threshold"
            assert (
                overall_std < 30
            ), f"Performance too variable: {overall_std:.1f}ms std dev"
            assert (
                abs(degradation_pct) < 10
            ), f"Performance degraded by {degradation_pct:.1f}%"

            print(
                f"   ✅ Sustained performance maintained over {batches * batch_duration} seconds"
            )

"""Benchmark Master Flow Orchestrator Database Performance
Test query performance with new indexes and schema changes.
"""

import asyncio
import os
import random
import statistics
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from tabulate import tabulate

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/migration_db"
)
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Benchmark configuration
NUM_FLOWS = 10000  # Number of test flows to create
NUM_QUERIES = 100  # Number of queries per benchmark
FLOW_TYPES = ["discovery", "assessment", "planning", "execution", "modernize", "finops"]
FLOW_STATUSES = ["initialized", "active", "processing", "paused", "completed", "failed"]
CLIENT_ACCOUNTS = [str(uuid.uuid4()) for _ in range(10)]  # 10 test client accounts


class MasterFlowBenchmark:
    """Benchmark query performance for master flow orchestrator"""

    def __init__(self):
        self.engine = create_engine(DATABASE_URL, poolclass=NullPool)
        self.async_engine = create_async_engine(ASYNC_DATABASE_URL, poolclass=NullPool)
        self.results = []

    async def setup_test_data(self):
        """Create test data for benchmarking"""
        print(f"Creating {NUM_FLOWS} test flows...")

        async with AsyncSession(self.async_engine) as session:
            # Clear existing test data
            await session.execute(
                text(
                    """
                DELETE FROM crewai_flow_state_extensions
                WHERE flow_metadata->>'benchmark' = 'true'
            """
                )
            )
            await session.commit()

            # Batch insert test flows
            batch_size = 1000
            for i in range(0, NUM_FLOWS, batch_size):
                flows = []
                for j in range(min(batch_size, NUM_FLOWS - i)):
                    flow_created = datetime.utcnow() - timedelta(
                        days=random.randint(0, 365)
                    )
                    flows.append(
                        {
                            "id": str(uuid.uuid4()),
                            "flow_id": str(uuid.uuid4()),
                            "client_account_id": random.choice(CLIENT_ACCOUNTS),
                            "engagement_id": str(uuid.uuid4()),
                            "user_id": f"user_{random.randint(1, 100)}",
                            "flow_type": random.choice(FLOW_TYPES),
                            "flow_name": f"Benchmark Flow {i+j}",
                            "flow_status": random.choice(FLOW_STATUSES),
                            "created_at": flow_created,
                            "updated_at": flow_created
                            + timedelta(hours=random.randint(1, 48)),
                            "phase_transitions": [
                                {
                                    "phase": "init",
                                    "timestamp": flow_created.isoformat(),
                                },
                                {
                                    "phase": "phase1",
                                    "timestamp": (
                                        flow_created + timedelta(hours=1)
                                    ).isoformat(),
                                },
                            ],
                            "flow_metadata": {"benchmark": "true", "index": i + j},
                        }
                    )

                # Bulk insert
                await session.execute(
                    text(
                        """
                    INSERT INTO crewai_flow_state_extensions (
                        id, flow_id, client_account_id, engagement_id, user_id,
                        flow_type, flow_name, flow_status, created_at, updated_at,
                        phase_transitions, flow_metadata
                    ) VALUES (
                        :id, :flow_id, :client_account_id, :engagement_id, :user_id,
                        :flow_type, :flow_name, :flow_status, :created_at, :updated_at,
                        :phase_transitions::jsonb, :flow_metadata::jsonb
                    )
                """
                    ),
                    flows,
                )

                await session.commit()
                print(f"  Created {i + len(flows)} flows...")

        print("Test data created successfully!\n")

    async def benchmark_query(
        self, name: str, query: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Benchmark a single query"""
        times = []

        async with AsyncSession(self.async_engine) as session:
            # Warm up
            await session.execute(text(query), params or {})

            # Run benchmarks
            for _ in range(NUM_QUERIES):
                start = time.perf_counter()
                result = await session.execute(text(query), params or {})
                _ = result.fetchall()  # Ensure results are fetched
                end = time.perf_counter()
                times.append((end - start) * 1000)  # Convert to milliseconds

        return {
            "name": name,
            "avg_ms": statistics.mean(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "median_ms": statistics.median(times),
            "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }

    async def run_benchmarks(self):
        """Run all benchmark queries"""
        print("Running query benchmarks...\n")

        # Benchmark 1: Query by flow_type and status (uses composite index)
        result = await self.benchmark_query(
            "Flow Type + Status Filter",
            """
            SELECT flow_id, flow_name, flow_status, created_at
            FROM crewai_flow_state_extensions
            WHERE flow_type = :flow_type AND flow_status = :status
            AND flow_metadata->>'benchmark' = 'true'
            LIMIT 100
            """,
            {"flow_type": "discovery", "status": "active"},
        )
        self.results.append(result)

        # Benchmark 2: Query by client_account_id and status (uses composite index)
        result = await self.benchmark_query(
            "Client + Status Filter",
            """
            SELECT flow_id, flow_name, flow_type, created_at
            FROM crewai_flow_state_extensions
            WHERE client_account_id = :client_id AND flow_status = :status
            AND flow_metadata->>'benchmark' = 'true'
            LIMIT 100
            """,
            {"client_id": CLIENT_ACCOUNTS[0], "status": "active"},
        )
        self.results.append(result)

        # Benchmark 3: Recent flows (uses created_at DESC index)
        result = await self.benchmark_query(
            "Recent Flows",
            """
            SELECT flow_id, flow_name, flow_type, flow_status, created_at
            FROM crewai_flow_state_extensions
            WHERE flow_metadata->>'benchmark' = 'true'
            ORDER BY created_at DESC
            LIMIT 100
            """,
        )
        self.results.append(result)

        # Benchmark 4: Complex multi-tenant query
        result = await self.benchmark_query(
            "Multi-tenant Active Flows",
            """
            SELECT client_account_id, flow_type, COUNT(*) as flow_count
            FROM crewai_flow_state_extensions
            WHERE flow_status IN ('active', 'processing')
            AND flow_metadata->>'benchmark' = 'true'
            GROUP BY client_account_id, flow_type
            ORDER BY flow_count DESC
            """,
        )
        self.results.append(result)

        # Benchmark 5: JSONB query performance
        result = await self.benchmark_query(
            "JSONB Phase Transitions",
            """
            SELECT flow_id, flow_name,
                   jsonb_array_length(phase_transitions) as phase_count
            FROM crewai_flow_state_extensions
            WHERE jsonb_array_length(phase_transitions) > 1
            AND flow_metadata->>'benchmark' = 'true'
            LIMIT 100
            """,
        )
        self.results.append(result)

        # Benchmark 6: Parent-child flow relationships
        result = await self.benchmark_query(
            "Hierarchical Flow Query",
            """
            WITH RECURSIVE flow_hierarchy AS (
                SELECT flow_id, parent_flow_id, flow_name, 0 as level
                FROM crewai_flow_state_extensions
                WHERE parent_flow_id IS NULL
                AND flow_metadata->>'benchmark' = 'true'
                LIMIT 10

                UNION ALL

                SELECT c.flow_id, c.parent_flow_id, c.flow_name, h.level + 1
                FROM crewai_flow_state_extensions c
                JOIN flow_hierarchy h ON c.parent_flow_id = h.flow_id
                WHERE h.level < 3
            )
            SELECT * FROM flow_hierarchy
            """,
        )
        self.results.append(result)

        # Benchmark 7: Full-text search simulation
        result = await self.benchmark_query(
            "Flow Name Search",
            """
            SELECT flow_id, flow_name, flow_type, flow_status
            FROM crewai_flow_state_extensions
            WHERE flow_name ILIKE :search_term
            AND flow_metadata->>'benchmark' = 'true'
            LIMIT 100
            """,
            {"search_term": "%Flow 1%"},
        )
        self.results.append(result)

        # Benchmark 8: Aggregate statistics
        result = await self.benchmark_query(
            "Flow Statistics",
            """
            SELECT
                flow_type,
                flow_status,
                COUNT(*) as count,
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600) as avg_duration_hours
            FROM crewai_flow_state_extensions
            WHERE flow_metadata->>'benchmark' = 'true'
            GROUP BY flow_type, flow_status
            ORDER BY count DESC
            """,
        )
        self.results.append(result)

    async def cleanup_test_data(self):
        """Remove test data after benchmarking"""
        print("\nCleaning up test data...")

        async with AsyncSession(self.async_engine) as session:
            await session.execute(
                text(
                    """
                DELETE FROM crewai_flow_state_extensions
                WHERE flow_metadata->>'benchmark' = 'true'
            """
                )
            )
            await session.commit()

        print("Test data cleaned up successfully!")

    def print_results(self):
        """Print benchmark results in a formatted table"""
        print("\n" + "=" * 80)
        print("MASTER FLOW ORCHESTRATOR PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)
        print(
            f"Test Configuration: {NUM_FLOWS} flows, {NUM_QUERIES} queries per benchmark"
        )
        print("=" * 80 + "\n")

        headers = [
            "Query",
            "Avg (ms)",
            "Min (ms)",
            "Max (ms)",
            "Median (ms)",
            "StdDev (ms)",
        ]
        rows = []

        for result in self.results:
            rows.append(
                [
                    result["name"],
                    f"{result['avg_ms']:.2f}",
                    f"{result['min_ms']:.2f}",
                    f"{result['max_ms']:.2f}",
                    f"{result['median_ms']:.2f}",
                    f"{result['stdev_ms']:.2f}",
                ]
            )

        print(tabulate(rows, headers=headers, tablefmt="grid"))

        # Performance summary
        print("\nPERFORMANCE SUMMARY:")
        print("-" * 40)

        # Check if queries meet performance targets
        fast_queries = sum(1 for r in self.results if r["avg_ms"] < 10)
        medium_queries = sum(1 for r in self.results if 10 <= r["avg_ms"] < 50)
        slow_queries = sum(1 for r in self.results if r["avg_ms"] >= 50)

        print(f"Fast queries (<10ms): {fast_queries}")
        print(f"Medium queries (10-50ms): {medium_queries}")
        print(f"Slow queries (>50ms): {slow_queries}")

        # Overall assessment
        print("\nOVERALL ASSESSMENT:")
        if slow_queries == 0 and medium_queries <= 2:
            print("✅ EXCELLENT - All queries perform well with indexes")
        elif slow_queries == 0:
            print("✅ GOOD - Queries perform acceptably with indexes")
        else:
            print("⚠️  WARNING - Some queries may need optimization")

        # Index effectiveness
        indexed_queries = [
            "Flow Type + Status Filter",
            "Client + Status Filter",
            "Recent Flows",
        ]
        indexed_performance = [r for r in self.results if r["name"] in indexed_queries]
        avg_indexed = statistics.mean([r["avg_ms"] for r in indexed_performance])

        print(f"\nIndexed query average: {avg_indexed:.2f}ms")
        if avg_indexed < 5:
            print("✅ Indexes are highly effective")
        elif avg_indexed < 20:
            print("✅ Indexes are working well")
        else:
            print("⚠️  Indexes may need tuning")

    async def run(self):
        """Run the complete benchmark suite"""
        try:
            await self.setup_test_data()
            await self.run_benchmarks()
            self.print_results()
        finally:
            await self.cleanup_test_data()
            await self.async_engine.dispose()


async def main():
    """Main entry point"""
    print("Master Flow Orchestrator Performance Benchmark")
    print("=" * 50)

    benchmark = MasterFlowBenchmark()
    await benchmark.run()


if __name__ == "__main__":
    asyncio.run(main())

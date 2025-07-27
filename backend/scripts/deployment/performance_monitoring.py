#!/usr/bin/env python3
"""
Discovery Flow Performance Monitoring and Alerting

This script provides performance monitoring and alerting for the discovery flow system,
focusing on query performance, constraint impact, and system health metrics.

Features:
1. Query performance benchmarking
2. Constraint impact analysis
3. Real-time performance monitoring
4. Automated alerting for performance degradation
5. Performance trend analysis

Usage:
    python scripts/deployment/performance_monitoring.py --benchmark
    python scripts/deployment/performance_monitoring.py --monitor --interval 60
    python scripts/deployment/performance_monitoring.py --analyze --days 7
    python scripts/deployment/performance_monitoring.py --alert-thresholds performance_thresholds.json
"""

import argparse
import asyncio
import json
import logging
import statistics
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    from app.core.database import AsyncSessionLocal
    from app.models.asset import Asset
    from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
    from app.models.data_import.core import DataImport, RawImportRecord
    from app.models.discovery_flow import DiscoveryFlow
except ImportError as e:
    logger.error(f"Failed to import application modules: {e}")
    logger.error("Make sure to run this script from the backend directory")
    exit(1)


class PerformanceMonitor:
    """
    Performance monitoring system for discovery flow data integrity operations.

    This class provides comprehensive performance monitoring including:
    - Query execution time tracking
    - Constraint enforcement impact measurement
    - System load and throughput analysis
    - Performance trend detection
    - Automated alerting for performance issues
    """

    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize the performance monitor.

        Args:
            alert_thresholds: Dictionary of performance thresholds for alerting
        """
        self.alert_thresholds = alert_thresholds or {
            "query_execution_time_ms": 500,  # Alert if queries take > 500ms
            "constraint_check_time_ms": 100,  # Alert if constraint checks take > 100ms
            "join_query_time_ms": 1000,  # Alert if join queries take > 1s
            "batch_operation_time_ms": 2000,  # Alert if batch operations take > 2s
            "cpu_usage_percent": 80,  # Alert if CPU usage > 80%
            "memory_usage_percent": 85,  # Alert if memory usage > 85%
            "active_connections": 100,  # Alert if active connections > 100
        }

        self.performance_history = []
        self.alerts = []

    async def run_performance_benchmark(self) -> Dict[str, Any]:
        """
        Run comprehensive performance benchmark tests.

        Returns:
            Dict containing benchmark results and performance metrics
        """
        logger.info("🚀 Starting performance benchmark tests...")

        start_time = datetime.now()
        benchmark_results = {
            "timestamp": start_time.isoformat(),
            "benchmark_id": str(uuid.uuid4()),
            "tests": {},
            "summary": {},
            "recommendations": [],
        }

        async with AsyncSessionLocal() as session:
            try:
                # 1. Basic query performance tests
                logger.info("📊 Running basic query performance tests...")
                basic_perf = await self._benchmark_basic_queries(session)
                benchmark_results["tests"]["basic_queries"] = basic_perf

                # 2. Join query performance tests
                logger.info("🔗 Running join query performance tests...")
                join_perf = await self._benchmark_join_queries(session)
                benchmark_results["tests"]["join_queries"] = join_perf

                # 3. Constraint impact tests
                logger.info("🛡️ Running constraint impact tests...")
                constraint_perf = await self._benchmark_constraint_impact(session)
                benchmark_results["tests"]["constraint_impact"] = constraint_perf

                # 4. Aggregation query tests
                logger.info("📈 Running aggregation query tests...")
                aggregation_perf = await self._benchmark_aggregation_queries(session)
                benchmark_results["tests"]["aggregation_queries"] = aggregation_perf

                # 5. Batch operation tests
                logger.info("📦 Running batch operation tests...")
                batch_perf = await self._benchmark_batch_operations(session)
                benchmark_results["tests"]["batch_operations"] = batch_perf

                # 6. Concurrent operation tests
                logger.info("⚡ Running concurrent operation tests...")
                concurrent_perf = await self._benchmark_concurrent_operations(session)
                benchmark_results["tests"]["concurrent_operations"] = concurrent_perf

                # Generate summary and recommendations
                benchmark_results["summary"] = self._generate_benchmark_summary(
                    benchmark_results["tests"]
                )
                benchmark_results["recommendations"] = (
                    self._generate_performance_recommendations(
                        benchmark_results["tests"]
                    )
                )

                total_duration = (datetime.now() - start_time).total_seconds()
                benchmark_results["total_duration_seconds"] = total_duration

                logger.info(
                    f"✅ Performance benchmark completed in {total_duration:.2f}s"
                )

                return benchmark_results

            except Exception as e:
                logger.error(f"❌ Performance benchmark failed: {e}")
                benchmark_results["error"] = str(e)
                return benchmark_results

    async def _benchmark_basic_queries(self, session: AsyncSession) -> Dict[str, Any]:
        """Benchmark basic query operations"""
        test_results = {}

        # Test 1: Master flow count query
        start_time = time.perf_counter()

        count_query = select(func.count(CrewAIFlowStateExtensions.id))
        result = await session.execute(count_query)
        master_flow_count = result.scalar()

        count_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["master_flow_count"] = {
            "execution_time_ms": count_time_ms,
            "record_count": master_flow_count,
            "alert": count_time_ms > self.alert_thresholds["query_execution_time_ms"],
        }

        # Test 2: Discovery flow listing with filter
        start_time = time.perf_counter()

        discovery_query = (
            select(DiscoveryFlow).where(DiscoveryFlow.status == "active").limit(100)
        )

        result = await session.execute(discovery_query)
        discovery_flows = result.scalars().all()

        discovery_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["discovery_flow_listing"] = {
            "execution_time_ms": discovery_time_ms,
            "record_count": len(discovery_flows),
            "alert": discovery_time_ms
            > self.alert_thresholds["query_execution_time_ms"],
        }

        # Test 3: Data import status query
        start_time = time.perf_counter()

        import_query = select(
            DataImport.status, func.count(DataImport.id).label("count")
        ).group_by(DataImport.status)

        result = await session.execute(import_query)
        import_stats = result.all()

        import_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["data_import_status"] = {
            "execution_time_ms": import_time_ms,
            "status_groups": len(import_stats),
            "alert": import_time_ms > self.alert_thresholds["query_execution_time_ms"],
        }

        # Test 4: Asset search query
        start_time = time.perf_counter()

        asset_query = (
            select(Asset).where(Asset.migration_readiness_score >= 0.7).limit(50)
        )

        result = await session.execute(asset_query)
        ready_assets = result.scalars().all()

        asset_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["asset_search"] = {
            "execution_time_ms": asset_time_ms,
            "record_count": len(ready_assets),
            "alert": asset_time_ms > self.alert_thresholds["query_execution_time_ms"],
        }

        return test_results

    async def _benchmark_join_queries(self, session: AsyncSession) -> Dict[str, Any]:
        """Benchmark join query operations"""
        test_results = {}

        # Test 1: Discovery flow with data import join
        start_time = time.perf_counter()

        discovery_import_query = (
            select(
                DiscoveryFlow.flow_id,
                DiscoveryFlow.flow_name,
                DiscoveryFlow.status,
                DataImport.import_name,
                DataImport.status.label("import_status"),
            )
            .select_from(DiscoveryFlow)
            .join(DataImport, DiscoveryFlow.data_import_id == DataImport.id)
            .limit(100)
        )

        result = await session.execute(discovery_import_query)
        discovery_import_results = result.all()

        discovery_import_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["discovery_flow_data_import_join"] = {
            "execution_time_ms": discovery_import_time_ms,
            "record_count": len(discovery_import_results),
            "alert": discovery_import_time_ms
            > self.alert_thresholds["join_query_time_ms"],
        }

        # Test 2: Master flow with all related entities
        start_time = time.perf_counter()

        master_flow_full_query = (
            select(
                CrewAIFlowStateExtensions.flow_id,
                CrewAIFlowStateExtensions.flow_name,
                CrewAIFlowStateExtensions.flow_status,
                DiscoveryFlow.flow_name.label("discovery_name"),
                DataImport.import_name,
                func.count(Asset.id).label("asset_count"),
            )
            .select_from(CrewAIFlowStateExtensions)
            .outerjoin(
                DiscoveryFlow,
                DiscoveryFlow.master_flow_id == CrewAIFlowStateExtensions.flow_id,
            )
            .outerjoin(DataImport, DiscoveryFlow.data_import_id == DataImport.id)
            .outerjoin(Asset, Asset.discovery_flow_id == DiscoveryFlow.flow_id)
            .group_by(
                CrewAIFlowStateExtensions.flow_id,
                CrewAIFlowStateExtensions.flow_name,
                CrewAIFlowStateExtensions.flow_status,
                DiscoveryFlow.flow_name,
                DataImport.import_name,
            )
            .limit(50)
        )

        result = await session.execute(master_flow_full_query)
        master_flow_results = result.all()

        master_flow_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["master_flow_full_join"] = {
            "execution_time_ms": master_flow_time_ms,
            "record_count": len(master_flow_results),
            "alert": master_flow_time_ms > self.alert_thresholds["join_query_time_ms"],
        }

        # Test 3: Asset with raw record join
        start_time = time.perf_counter()

        asset_raw_query = (
            select(
                Asset.asset_name,
                Asset.hostname,
                Asset.migration_readiness_score,
                RawImportRecord.raw_data,
            )
            .select_from(Asset)
            .join(RawImportRecord, Asset.raw_import_record_id == RawImportRecord.id)
            .where(Asset.migration_readiness_score >= 0.8)
            .limit(100)
        )

        result = await session.execute(asset_raw_query)
        asset_raw_results = result.all()

        asset_raw_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["asset_raw_record_join"] = {
            "execution_time_ms": asset_raw_time_ms,
            "record_count": len(asset_raw_results),
            "alert": asset_raw_time_ms > self.alert_thresholds["join_query_time_ms"],
        }

        return test_results

    async def _benchmark_constraint_impact(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """Benchmark constraint enforcement impact"""
        test_results = {}

        # Test 1: Foreign key constraint validation time
        start_time = time.perf_counter()

        # Query that exercises foreign key constraints
        constraint_query = (
            select(func.count(DataImport.id).label("valid_imports"))
            .select_from(DataImport)
            .join(
                CrewAIFlowStateExtensions,
                DataImport.master_flow_id == CrewAIFlowStateExtensions.flow_id,
            )
        )

        result = await session.execute(constraint_query)
        valid_imports = result.scalar()

        constraint_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["foreign_key_validation"] = {
            "execution_time_ms": constraint_time_ms,
            "valid_records": valid_imports,
            "alert": constraint_time_ms
            > self.alert_thresholds["constraint_check_time_ms"],
        }

        # Test 2: Constraint-heavy insert simulation
        start_time = time.perf_counter()

        # Create a test master flow
        test_master_flow = CrewAIFlowStateExtensions(
            flow_id=str(uuid.uuid4()),
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id="performance_test_user",
            flow_type="test",
            flow_name="Performance Test Flow",
            flow_status="active",
        )

        session.add(test_master_flow)
        await session.commit()
        await session.refresh(test_master_flow)

        # Create related data import (exercises constraint)
        test_data_import = DataImport(
            client_account_id=test_master_flow.client_account_id,
            engagement_id=test_master_flow.engagement_id,
            master_flow_id=test_master_flow.flow_id,
            import_name="Performance Test Import",
            import_type="test",
            filename="performance_test.csv",
            status="completed",
            imported_by="performance_test_user",
            total_records=1,
        )

        session.add(test_data_import)
        await session.commit()

        constraint_insert_time_ms = (time.perf_counter() - start_time) * 1000

        # Cleanup
        await session.delete(test_data_import)
        await session.delete(test_master_flow)
        await session.commit()

        test_results["constraint_insert_validation"] = {
            "execution_time_ms": constraint_insert_time_ms,
            "alert": constraint_insert_time_ms
            > self.alert_thresholds["constraint_check_time_ms"],
        }

        return test_results

    async def _benchmark_aggregation_queries(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """Benchmark aggregation query operations"""
        test_results = {}

        # Test 1: Discovery flow statistics
        start_time = time.perf_counter()

        discovery_stats_query = select(
            DiscoveryFlow.status,
            func.count(DiscoveryFlow.id).label("count"),
            func.avg(DiscoveryFlow.progress_percentage).label("avg_progress"),
            func.max(DiscoveryFlow.progress_percentage).label("max_progress"),
            func.min(DiscoveryFlow.progress_percentage).label("min_progress"),
        ).group_by(DiscoveryFlow.status)

        result = await session.execute(discovery_stats_query)
        discovery_stats = result.all()

        discovery_stats_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["discovery_flow_statistics"] = {
            "execution_time_ms": discovery_stats_time_ms,
            "status_groups": len(discovery_stats),
            "alert": discovery_stats_time_ms
            > self.alert_thresholds["query_execution_time_ms"],
        }

        # Test 2: Asset migration readiness analysis
        start_time = time.perf_counter()

        asset_readiness_query = select(
            func.count(Asset.id).label("total_assets"),
            func.avg(Asset.migration_readiness_score).label("avg_readiness"),
            func.count(func.case((Asset.migration_readiness_score >= 0.8, 1))).label(
                "high_readiness"
            ),
            func.count(func.case((Asset.migration_readiness_score >= 0.6, 1))).label(
                "medium_readiness"
            ),
            func.count(func.case((Asset.migration_readiness_score < 0.6, 1))).label(
                "low_readiness"
            ),
        )

        result = await session.execute(asset_readiness_query)
        asset_readiness = result.first()

        asset_readiness_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["asset_readiness_analysis"] = {
            "execution_time_ms": asset_readiness_time_ms,
            "total_assets": asset_readiness.total_assets if asset_readiness else 0,
            "alert": asset_readiness_time_ms
            > self.alert_thresholds["query_execution_time_ms"],
        }

        # Test 3: Data import volume analysis
        start_time = time.perf_counter()

        import_volume_query = select(
            DataImport.import_type,
            func.count(DataImport.id).label("import_count"),
            func.sum(DataImport.total_records).label("total_records"),
            func.avg(DataImport.total_records).label("avg_records_per_import"),
            func.sum(DataImport.file_size).label("total_file_size"),
        ).group_by(DataImport.import_type)

        result = await session.execute(import_volume_query)
        import_volume = result.all()

        import_volume_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["data_import_volume_analysis"] = {
            "execution_time_ms": import_volume_time_ms,
            "import_types": len(import_volume),
            "alert": import_volume_time_ms
            > self.alert_thresholds["query_execution_time_ms"],
        }

        return test_results

    async def _benchmark_batch_operations(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """Benchmark batch operation performance"""
        test_results = {}

        # Test 1: Batch insert performance
        start_time = time.perf_counter()

        # Create test master flow
        test_master_flow = CrewAIFlowStateExtensions(
            flow_id=str(uuid.uuid4()),
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id="batch_test_user",
            flow_type="test",
            flow_name="Batch Test Flow",
            flow_status="active",
        )

        session.add(test_master_flow)
        await session.commit()
        await session.refresh(test_master_flow)

        # Batch insert data imports
        batch_imports = []
        for i in range(20):
            data_import = DataImport(
                client_account_id=test_master_flow.client_account_id,
                engagement_id=test_master_flow.engagement_id,
                master_flow_id=test_master_flow.flow_id,
                import_name=f"Batch Test Import {i+1}",
                import_type="test",
                filename=f"batch_test_{i+1}.csv",
                status="pending",
                imported_by="batch_test_user",
                total_records=100,
            )
            batch_imports.append(data_import)
            session.add(data_import)

        await session.commit()

        batch_insert_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["batch_insert"] = {
            "execution_time_ms": batch_insert_time_ms,
            "records_inserted": len(batch_imports),
            "alert": batch_insert_time_ms
            > self.alert_thresholds["batch_operation_time_ms"],
        }

        # Test 2: Batch update performance
        start_time = time.perf_counter()

        for data_import in batch_imports:
            data_import.status = "completed"
            data_import.progress_percentage = 100.0

        await session.commit()

        batch_update_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["batch_update"] = {
            "execution_time_ms": batch_update_time_ms,
            "records_updated": len(batch_imports),
            "alert": batch_update_time_ms
            > self.alert_thresholds["batch_operation_time_ms"],
        }

        # Test 3: Batch delete performance (cleanup)
        start_time = time.perf_counter()

        for data_import in batch_imports:
            await session.delete(data_import)

        await session.delete(test_master_flow)
        await session.commit()

        batch_delete_time_ms = (time.perf_counter() - start_time) * 1000

        test_results["batch_delete"] = {
            "execution_time_ms": batch_delete_time_ms,
            "records_deleted": len(batch_imports) + 1,
            "alert": batch_delete_time_ms
            > self.alert_thresholds["batch_operation_time_ms"],
        }

        return test_results

    async def _benchmark_concurrent_operations(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """Benchmark concurrent operation performance"""
        test_results = {}

        # Test 1: Concurrent read operations
        start_time = time.perf_counter()

        # Simulate concurrent reads
        concurrent_tasks = []
        for i in range(5):
            task = asyncio.create_task(self._concurrent_read_task(session))
            concurrent_tasks.append(task)

        concurrent_results = await asyncio.gather(
            *concurrent_tasks, return_exceptions=True
        )

        concurrent_read_time_ms = (time.perf_counter() - start_time) * 1000

        successful_reads = sum(
            1 for result in concurrent_results if not isinstance(result, Exception)
        )

        test_results["concurrent_reads"] = {
            "execution_time_ms": concurrent_read_time_ms,
            "concurrent_operations": len(concurrent_tasks),
            "successful_operations": successful_reads,
            "alert": concurrent_read_time_ms
            > self.alert_thresholds["query_execution_time_ms"] * 2,
        }

        return test_results

    async def _concurrent_read_task(self, session: AsyncSession) -> int:
        """Individual concurrent read task"""
        query = select(func.count(CrewAIFlowStateExtensions.id))
        result = await session.execute(query)
        return result.scalar()

    def _generate_benchmark_summary(
        self, test_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary of benchmark results"""
        total_tests = 0
        failed_tests = 0
        total_alerts = 0

        execution_times = []

        for category, tests in test_results.items():
            for test_name, test_data in tests.items():
                total_tests += 1

                if test_data.get("alert", False):
                    total_alerts += 1

                if "error" in test_data:
                    failed_tests += 1

                if "execution_time_ms" in test_data:
                    execution_times.append(test_data["execution_time_ms"])

        return {
            "total_tests": total_tests,
            "failed_tests": failed_tests,
            "total_alerts": total_alerts,
            "success_rate": (
                ((total_tests - failed_tests) / total_tests * 100)
                if total_tests > 0
                else 0
            ),
            "average_execution_time_ms": (
                statistics.mean(execution_times) if execution_times else 0
            ),
            "median_execution_time_ms": (
                statistics.median(execution_times) if execution_times else 0
            ),
            "max_execution_time_ms": max(execution_times) if execution_times else 0,
            "min_execution_time_ms": min(execution_times) if execution_times else 0,
        }

    def _generate_performance_recommendations(
        self, test_results: Dict[str, Any]
    ) -> List[str]:
        """Generate performance recommendations based on test results"""
        recommendations = []

        # Check for slow queries
        slow_queries = []
        for category, tests in test_results.items():
            for test_name, test_data in tests.items():
                if test_data.get("alert", False) and "execution_time_ms" in test_data:
                    slow_queries.append(
                        (category, test_name, test_data["execution_time_ms"])
                    )

        if slow_queries:
            recommendations.append(
                f"Optimize slow queries: {len(slow_queries)} queries exceeded performance thresholds"
            )

            # Sort by execution time and recommend top 3
            slow_queries.sort(key=lambda x: x[2], reverse=True)
            for category, test_name, time_ms in slow_queries[:3]:
                recommendations.append(
                    f"  - {category}.{test_name}: {time_ms:.2f}ms (consider adding indexes or optimizing query)"
                )

        # Check join query performance
        join_tests = test_results.get("join_queries", {})
        slow_joins = [
            test
            for test, data in join_tests.items()
            if data.get("execution_time_ms", 0) > 1000
        ]

        if slow_joins:
            recommendations.append(
                "Consider optimizing join queries - multiple joins taking >1s detected"
            )
            recommendations.append("  - Review foreign key indexes on joined columns")
            recommendations.append("  - Consider query optimization or result caching")

        # Check batch operation performance
        batch_tests = test_results.get("batch_operations", {})
        slow_batches = [
            test
            for test, data in batch_tests.items()
            if data.get("execution_time_ms", 0) > 2000
        ]

        if slow_batches:
            recommendations.append(
                "Batch operations are slow - consider optimizing bulk operations"
            )
            recommendations.append("  - Use bulk insert/update methods where possible")
            recommendations.append("  - Consider batching operations in smaller chunks")

        # Check constraint impact
        constraint_tests = test_results.get("constraint_impact", {})
        slow_constraints = [
            test
            for test, data in constraint_tests.items()
            if data.get("execution_time_ms", 0) > 100
        ]

        if slow_constraints:
            recommendations.append("Foreign key constraint validation is slow")
            recommendations.append(
                "  - Ensure proper indexes exist on foreign key columns"
            )
            recommendations.append(
                "  - Consider constraint deferral for bulk operations"
            )

        if not recommendations:
            recommendations.append(
                "No performance issues detected - system performing well"
            )

        return recommendations

    async def monitor_real_time_performance(
        self, interval_seconds: int = 60, duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Monitor real-time performance metrics.

        Args:
            interval_seconds: Monitoring interval in seconds
            duration_minutes: Total monitoring duration in minutes

        Returns:
            Dict containing monitoring results and alerts
        """
        logger.info(
            f"🔍 Starting real-time performance monitoring for {duration_minutes} minutes..."
        )

        monitoring_results = {
            "start_time": datetime.now().isoformat(),
            "interval_seconds": interval_seconds,
            "duration_minutes": duration_minutes,
            "measurements": [],
            "alerts": [],
            "summary": {},
        }

        end_time = datetime.now() + timedelta(minutes=duration_minutes)

        while datetime.now() < end_time:
            measurement_start = datetime.now()

            try:
                # Take performance measurement
                measurement = await self._take_performance_measurement()
                measurement["timestamp"] = measurement_start.isoformat()

                monitoring_results["measurements"].append(measurement)

                # Check for alerts
                alerts = self._check_performance_alerts(measurement)
                monitoring_results["alerts"].extend(alerts)

                if alerts:
                    for alert in alerts:
                        logger.warning(f"🚨 Performance Alert: {alert['message']}")

                logger.info(
                    f"📊 Performance measurement: avg_query_time={measurement.get('avg_query_time_ms', 0):.2f}ms"
                )

            except Exception as e:
                logger.error(f"❌ Error taking performance measurement: {e}")
                monitoring_results["alerts"].append(
                    {
                        "timestamp": measurement_start.isoformat(),
                        "type": "monitoring_error",
                        "message": f"Failed to take performance measurement: {e}",
                    }
                )

            # Wait for next interval
            await asyncio.sleep(interval_seconds)

        # Generate summary
        monitoring_results["summary"] = self._generate_monitoring_summary(
            monitoring_results["measurements"]
        )
        monitoring_results["end_time"] = datetime.now().isoformat()

        logger.info(
            f"✅ Real-time monitoring completed. {len(monitoring_results['alerts'])} alerts generated."
        )

        return monitoring_results

    async def _take_performance_measurement(self) -> Dict[str, Any]:
        """Take a single performance measurement"""
        measurement = {}

        async with AsyncSessionLocal() as session:
            # Measure query execution times
            query_times = []

            # Test query 1: Master flow count
            start_time = time.perf_counter()
            result = await session.execute(
                select(func.count(CrewAIFlowStateExtensions.id))
            )
            result.scalar()
            query_times.append((time.perf_counter() - start_time) * 1000)

            # Test query 2: Discovery flow listing
            start_time = time.perf_counter()
            result = await session.execute(select(DiscoveryFlow).limit(10))
            result.scalars().all()
            query_times.append((time.perf_counter() - start_time) * 1000)

            # Test query 3: Join query
            start_time = time.perf_counter()
            result = await session.execute(
                select(DiscoveryFlow.flow_id, DataImport.import_name)
                .select_from(DiscoveryFlow)
                .join(DataImport, DiscoveryFlow.data_import_id == DataImport.id)
                .limit(10)
            )
            result.all()
            join_time_ms = (time.perf_counter() - start_time) * 1000

            measurement.update(
                {
                    "avg_query_time_ms": statistics.mean(query_times),
                    "max_query_time_ms": max(query_times),
                    "min_query_time_ms": min(query_times),
                    "join_query_time_ms": join_time_ms,
                }
            )

            # Get database connection stats
            connection_stats = await self._get_connection_stats(session)
            measurement.update(connection_stats)

        return measurement

    async def _get_connection_stats(self, session: AsyncSession) -> Dict[str, Any]:
        """Get database connection statistics"""
        try:
            # Get active connection count
            connection_query = text(
                """
                SELECT
                    COUNT(*) as active_connections,
                    COUNT(CASE WHEN state = 'active' THEN 1 END) as active_queries,
                    COUNT(CASE WHEN state = 'idle' THEN 1 END) as idle_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """
            )

            result = await session.execute(connection_query)
            connection_stats = result.first()

            return {
                "active_connections": (
                    connection_stats.active_connections if connection_stats else 0
                ),
                "active_queries": (
                    connection_stats.active_queries if connection_stats else 0
                ),
                "idle_connections": (
                    connection_stats.idle_connections if connection_stats else 0
                ),
            }

        except Exception as e:
            logger.warning(f"Could not get connection stats: {e}")
            return {"active_connections": 0, "active_queries": 0, "idle_connections": 0}

    def _check_performance_alerts(
        self, measurement: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check measurement against alert thresholds"""
        alerts = []

        # Check query execution time
        if (
            measurement.get("avg_query_time_ms", 0)
            > self.alert_thresholds["query_execution_time_ms"]
        ):
            alerts.append(
                {
                    "timestamp": measurement.get("timestamp"),
                    "type": "slow_query",
                    "metric": "avg_query_time_ms",
                    "value": measurement["avg_query_time_ms"],
                    "threshold": self.alert_thresholds["query_execution_time_ms"],
                    "message": f"Average query time {measurement['avg_query_time_ms']:.2f}ms exceeds threshold {self.alert_thresholds['query_execution_time_ms']}ms",
                }
            )

        # Check join query time
        if (
            measurement.get("join_query_time_ms", 0)
            > self.alert_thresholds["join_query_time_ms"]
        ):
            alerts.append(
                {
                    "timestamp": measurement.get("timestamp"),
                    "type": "slow_join",
                    "metric": "join_query_time_ms",
                    "value": measurement["join_query_time_ms"],
                    "threshold": self.alert_thresholds["join_query_time_ms"],
                    "message": f"Join query time {measurement['join_query_time_ms']:.2f}ms exceeds threshold {self.alert_thresholds['join_query_time_ms']}ms",
                }
            )

        # Check connection count
        if (
            measurement.get("active_connections", 0)
            > self.alert_thresholds["active_connections"]
        ):
            alerts.append(
                {
                    "timestamp": measurement.get("timestamp"),
                    "type": "high_connections",
                    "metric": "active_connections",
                    "value": measurement["active_connections"],
                    "threshold": self.alert_thresholds["active_connections"],
                    "message": f"Active connections {measurement['active_connections']} exceeds threshold {self.alert_thresholds['active_connections']}",
                }
            )

        return alerts

    def _generate_monitoring_summary(
        self, measurements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of monitoring results"""
        if not measurements:
            return {"error": "No measurements available"}

        # Extract metrics
        query_times = [m.get("avg_query_time_ms", 0) for m in measurements]
        join_times = [m.get("join_query_time_ms", 0) for m in measurements]
        connection_counts = [m.get("active_connections", 0) for m in measurements]

        return {
            "total_measurements": len(measurements),
            "query_performance": {
                "avg_query_time_ms": statistics.mean(query_times),
                "median_query_time_ms": statistics.median(query_times),
                "max_query_time_ms": max(query_times),
                "min_query_time_ms": min(query_times),
            },
            "join_performance": {
                "avg_join_time_ms": statistics.mean(join_times),
                "median_join_time_ms": statistics.median(join_times),
                "max_join_time_ms": max(join_times),
                "min_join_time_ms": min(join_times),
            },
            "connection_stats": {
                "avg_connections": statistics.mean(connection_counts),
                "max_connections": max(connection_counts),
                "min_connections": min(connection_counts),
            },
        }


async def main():
    """Main function for performance monitoring"""
    parser = argparse.ArgumentParser(
        description="Discovery flow performance monitoring"
    )
    parser.add_argument(
        "--benchmark", action="store_true", help="Run performance benchmark"
    )
    parser.add_argument(
        "--monitor", action="store_true", help="Run real-time monitoring"
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="Monitoring interval in seconds"
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Monitoring duration in minutes"
    )
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument(
        "--alert-thresholds", help="JSON file with custom alert thresholds"
    )

    args = parser.parse_args()

    # Load custom alert thresholds if provided
    alert_thresholds = None
    if args.alert_thresholds:
        try:
            with open(args.alert_thresholds, "r") as f:
                alert_thresholds = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load alert thresholds: {e}")
            exit(1)

    # Initialize performance monitor
    monitor = PerformanceMonitor(alert_thresholds=alert_thresholds)

    try:
        results = None

        if args.benchmark:
            logger.info("🚀 Running performance benchmark...")
            results = await monitor.run_performance_benchmark()

        elif args.monitor:
            logger.info(
                f"🔍 Starting real-time monitoring (interval: {args.interval}s, duration: {args.duration}m)..."
            )
            results = await monitor.monitor_real_time_performance(
                interval_seconds=args.interval, duration_minutes=args.duration
            )

        else:
            logger.error("Please specify --benchmark or --monitor")
            exit(1)

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"📄 Results saved to {args.output}")
        else:
            print(json.dumps(results, indent=2, default=str))

        # Check for performance issues
        if results.get("summary", {}).get("total_alerts", 0) > 0:
            logger.warning("⚠️  Performance issues detected - see results for details")
            exit(1)
        else:
            logger.info("✅ No performance issues detected")
            exit(0)

    except Exception as e:
        logger.error(f"❌ Performance monitoring failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())

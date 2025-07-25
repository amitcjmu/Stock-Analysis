#!/usr/bin/env python3
"""
Performance Validation Tests

This script tests database and application performance with seeded demo data
to ensure acceptable response times for the AI Modernize Migration Platform.

Usage:
    python scripts/qa/performance_validation.py [--verbose] [--benchmark]
"""

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median
from typing import Any, Dict, List, Optional

# Add app path
sys.path.append('/app')

from sqlalchemy import and_, distinct, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import (
    Asset,
    ClientAccount,
    DataImport,
    DiscoveryFlow,
    Engagement,
    Migration,
    User,
)


@dataclass
class PerformanceResult:
    """Results of a performance test."""
    test_name: str
    execution_time: float
    record_count: int
    passed: bool
    threshold: float
    message: str
    details: Optional[Dict[str, Any]] = None

class PerformanceValidator:
    """Validate database and query performance with seeded data."""

    def __init__(self, verbose: bool = False, benchmark_mode: bool = False):
        self.verbose = verbose
        self.benchmark_mode = benchmark_mode
        self.results: List[PerformanceResult] = []

        # Performance thresholds (in seconds)
        self.thresholds = {
            'simple_count': 0.5,
            'simple_select': 1.0,
            'complex_join': 3.0,
            'aggregation': 2.0,
            'search_query': 2.0,
            'reporting_query': 5.0,
            'bulk_operation': 10.0
        }

        if benchmark_mode:
            # More relaxed thresholds for benchmark mode
            self.thresholds = {k: v * 2 for k, v in self.thresholds.items()}

    async def run_performance_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance validation tests."""
        print("⚡ Starting Performance Validation Tests...")
        print("=" * 60)

        async with AsyncSessionLocal() as session:
            # Basic query performance
            await self._test_simple_queries(session)

            # Complex join performance
            await self._test_complex_joins(session)

            # Aggregation performance
            await self._test_aggregation_queries(session)

            # Search and filtering performance
            await self._test_search_performance(session)

            # Reporting query performance
            await self._test_reporting_queries(session)

            # Bulk operation performance
            await self._test_bulk_operations(session)

            # Index effectiveness
            await self._test_index_performance(session)

            # Memory usage simulation
            await self._test_memory_usage(session)

        return self._generate_performance_report()

    async def _test_simple_queries(self, session: AsyncSession):
        """Test basic query performance."""
        print("🔍 Testing Simple Query Performance...")

        # Test 1: Simple count queries
        start_time = time.time()
        result = await session.execute(select(func.count(Asset.id)))
        asset_count = result.scalar()
        execution_time = time.time() - start_time

        self._add_result(
            "simple_count_assets",
            execution_time,
            asset_count,
            execution_time <= self.thresholds['simple_count'],
            self.thresholds['simple_count'],
            f"Asset count query: {asset_count} records in {execution_time:.3f}s"
        )

        # Test 2: Simple select with WHERE
        start_time = time.time()
        result = await session.execute(
            select(Asset.id, Asset.name, Asset.asset_type)
            .where(Asset.asset_type == 'Server')
            .limit(100)
        )
        servers = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "simple_select_servers",
            execution_time,
            len(servers),
            execution_time <= self.thresholds['simple_select'],
            self.thresholds['simple_select'],
            f"Server select query: {len(servers)} records in {execution_time:.3f}s"
        )

        # Test 3: User lookup by email (common operation)
        start_time = time.time()
        result = await session.execute(
            select(User).where(User.email.like('%@techcorp.com'))
        )
        users = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "simple_user_lookup",
            execution_time,
            len(users),
            execution_time <= self.thresholds['simple_select'],
            self.thresholds['simple_select'],
            f"User email lookup: {len(users)} records in {execution_time:.3f}s"
        )

    async def _test_complex_joins(self, session: AsyncSession):
        """Test complex join query performance."""
        print("🔗 Testing Complex Join Performance...")

        # Test 1: Asset with client and engagement info
        start_time = time.time()
        result = await session.execute(
            select(
                Asset.name,
                Asset.asset_type,
                Asset.current_monthly_cost,
                ClientAccount.company_name,
                Engagement.name.label('engagement_name'),
                Engagement.status
            )
            .join(ClientAccount, Asset.client_account_id == ClientAccount.id)
            .join(Engagement, Asset.engagement_id == Engagement.id)
            .order_by(Asset.current_monthly_cost.desc())
            .limit(100)
        )
        assets_with_context = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "complex_join_asset_context",
            execution_time,
            len(assets_with_context),
            execution_time <= self.thresholds['complex_join'],
            self.thresholds['complex_join'],
            f"Asset context join: {len(assets_with_context)} records in {execution_time:.3f}s"
        )

        # Test 2: Discovery flow with all related data
        start_time = time.time()
        result = await session.execute(
            select(
                DiscoveryFlow.flow_id,
                DiscoveryFlow.current_phase,
                DiscoveryFlow.progress_percentage,
                ClientAccount.company_name,
                Engagement.name.label('engagement_name'),
                DataImport.file_name,
                DataImport.status.label('import_status')
            )
            .join(ClientAccount, DiscoveryFlow.client_account_id == ClientAccount.id)
            .join(Engagement, DiscoveryFlow.engagement_id == Engagement.id)
            .outerjoin(DataImport, DiscoveryFlow.id == DataImport.master_flow_id)
            .order_by(DiscoveryFlow.created_at.desc())
        )
        flows_with_context = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "complex_join_discovery_flow",
            execution_time,
            len(flows_with_context),
            execution_time <= self.thresholds['complex_join'],
            self.thresholds['complex_join'],
            f"Discovery flow join: {len(flows_with_context)} records in {execution_time:.3f}s"
        )

        # Test 3: Asset dependencies with names
        start_time = time.time()
        result = await session.execute(
            select(
                Asset.name.label('asset_name'),
                Asset.asset_type,
                func.string_agg(Asset.name, ', ').label('depends_on')
            )
            .select_from(Asset)
            .outerjoin(AssetDependency, Asset.id == AssetDependency.asset_id)
            .outerjoin(Asset.alias('dependent'), AssetDependency.depends_on_asset_id == Asset.alias('dependent').id)
            .group_by(Asset.id, Asset.name, Asset.asset_type)
            .limit(50)
        )
        dependencies = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "complex_join_dependencies",
            execution_time,
            len(dependencies),
            execution_time <= self.thresholds['complex_join'],
            self.thresholds['complex_join'],
            f"Asset dependencies join: {len(dependencies)} records in {execution_time:.3f}s"
        )

    async def _test_aggregation_queries(self, session: AsyncSession):
        """Test aggregation query performance."""
        print("📊 Testing Aggregation Performance...")

        # Test 1: Asset statistics by client
        start_time = time.time()
        result = await session.execute(
            select(
                ClientAccount.company_name,
                func.count(Asset.id).label('asset_count'),
                func.count(distinct(Asset.asset_type)).label('unique_types'),
                func.avg(Asset.current_monthly_cost).label('avg_cost'),
                func.sum(Asset.current_monthly_cost).label('total_cost'),
                func.avg(Asset.cpu_utilization_percent).label('avg_cpu'),
                func.avg(Asset.memory_utilization_percent).label('avg_memory')
            )
            .select_from(ClientAccount)
            .join(Asset, ClientAccount.id == Asset.client_account_id)
            .group_by(ClientAccount.id, ClientAccount.company_name)
            .order_by(func.count(Asset.id).desc())
        )
        client_stats = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "aggregation_client_stats",
            execution_time,
            len(client_stats),
            execution_time <= self.thresholds['aggregation'],
            self.thresholds['aggregation'],
            f"Client asset statistics: {len(client_stats)} clients in {execution_time:.3f}s"
        )

        # Test 2: Monthly cost analysis by asset type
        start_time = time.time()
        result = await session.execute(
            select(
                Asset.asset_type,
                func.count(Asset.id).label('count'),
                func.avg(Asset.current_monthly_cost).label('avg_cost'),
                func.min(Asset.current_monthly_cost).label('min_cost'),
                func.max(Asset.current_monthly_cost).label('max_cost'),
                func.sum(Asset.current_monthly_cost).label('total_cost')
            )
            .where(Asset.asset_type.is_not(None))
            .group_by(Asset.asset_type)
            .order_by(func.sum(Asset.current_monthly_cost).desc())
        )
        cost_analysis = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "aggregation_cost_analysis",
            execution_time,
            len(cost_analysis),
            execution_time <= self.thresholds['aggregation'],
            self.thresholds['aggregation'],
            f"Cost analysis by type: {len(cost_analysis)} types in {execution_time:.3f}s"
        )

        # Test 3: Engagement progress summary
        start_time = time.time()
        result = await session.execute(
            select(
                Engagement.status,
                func.count(Engagement.id).label('engagement_count'),
                func.avg(DiscoveryFlow.progress_percentage).label('avg_progress'),
                func.count(distinct(Asset.id)).label('total_assets'),
                func.sum(Asset.current_monthly_cost).label('total_monthly_cost')
            )
            .select_from(Engagement)
            .outerjoin(DiscoveryFlow, Engagement.id == DiscoveryFlow.engagement_id)
            .outerjoin(Asset, Engagement.id == Asset.engagement_id)
            .group_by(Engagement.status)
            .order_by(func.count(Engagement.id).desc())
        )
        engagement_summary = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "aggregation_engagement_summary",
            execution_time,
            len(engagement_summary),
            execution_time <= self.thresholds['aggregation'],
            self.thresholds['aggregation'],
            f"Engagement summary: {len(engagement_summary)} statuses in {execution_time:.3f}s"
        )

    async def _test_search_performance(self, session: AsyncSession):
        """Test search and filtering performance."""
        print("🔍 Testing Search Performance...")

        # Test 1: Asset name search
        start_time = time.time()
        result = await session.execute(
            select(Asset.id, Asset.name, Asset.asset_type, Asset.current_monthly_cost)
            .where(Asset.name.ilike('%server%'))
            .order_by(Asset.current_monthly_cost.desc())
            .limit(50)
        )
        search_results = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "search_asset_name",
            execution_time,
            len(search_results),
            execution_time <= self.thresholds['search_query'],
            self.thresholds['search_query'],
            f"Asset name search: {len(search_results)} results in {execution_time:.3f}s"
        )

        # Test 2: Multi-field search with filters
        start_time = time.time()
        result = await session.execute(
            select(Asset.id, Asset.name, Asset.asset_type, ClientAccount.company_name)
            .join(ClientAccount, Asset.client_account_id == ClientAccount.id)
            .where(
                and_(
                    or_(
                        Asset.name.ilike('%prod%'),
                        Asset.asset_type.ilike('%server%')
                    ),
                    Asset.current_monthly_cost > 1000,
                    Asset.cpu_utilization_percent > 50
                )
            )
            .order_by(Asset.current_monthly_cost.desc())
            .limit(100)
        )
        filtered_results = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "search_multi_field",
            execution_time,
            len(filtered_results),
            execution_time <= self.thresholds['search_query'],
            self.thresholds['search_query'],
            f"Multi-field search: {len(filtered_results)} results in {execution_time:.3f}s"
        )

        # Test 3: Date range filtering
        start_time = time.time()
        result = await session.execute(
            select(DiscoveryFlow.id, DiscoveryFlow.flow_id, DiscoveryFlow.current_phase)
            .where(
                and_(
                    DiscoveryFlow.created_at >= func.now() - text("INTERVAL '30 days'"),
                    DiscoveryFlow.progress_percentage > 0
                )
            )
            .order_by(DiscoveryFlow.created_at.desc())
        )
        recent_flows = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "search_date_range",
            execution_time,
            len(recent_flows),
            execution_time <= self.thresholds['search_query'],
            self.thresholds['search_query'],
            f"Date range search: {len(recent_flows)} results in {execution_time:.3f}s"
        )

    async def _test_reporting_queries(self, session: AsyncSession):
        """Test complex reporting query performance."""
        print("📈 Testing Reporting Query Performance...")

        # Test 1: Comprehensive asset report
        start_time = time.time()
        result = await session.execute(
            select(
                Asset.id,
                Asset.name,
                Asset.asset_type,
                Asset.current_monthly_cost,
                Asset.cpu_utilization_percent,
                Asset.memory_utilization_percent,
                ClientAccount.company_name,
                ClientAccount.industry,
                Engagement.name.label('engagement_name'),
                Engagement.status.label('engagement_status'),
                DiscoveryFlow.current_phase,
                DiscoveryFlow.progress_percentage,
                Assessment.assessment_type,
                Assessment.confidence_level,
                Migration.current_phase.label('migration_phase')
            )
            .select_from(Asset)
            .join(ClientAccount, Asset.client_account_id == ClientAccount.id)
            .join(Engagement, Asset.engagement_id == Engagement.id)
            .outerjoin(DiscoveryFlow, Engagement.id == DiscoveryFlow.engagement_id)
            .outerjoin(Assessment, Asset.id == Assessment.asset_id)
            .outerjoin(Migration, Asset.migration_id == Migration.id)
            .order_by(Asset.current_monthly_cost.desc())
            .limit(200)
        )
        comprehensive_report = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "reporting_comprehensive_asset",
            execution_time,
            len(comprehensive_report),
            execution_time <= self.thresholds['reporting_query'],
            self.thresholds['reporting_query'],
            f"Comprehensive asset report: {len(comprehensive_report)} records in {execution_time:.3f}s"
        )

        # Test 2: Migration readiness dashboard
        start_time = time.time()
        result = await session.execute(
            select(
                ClientAccount.company_name,
                func.count(distinct(Asset.id)).label('total_assets'),
                func.count(distinct(
                    func.case((Assessment.id.is_not(None), Asset.id))
                )).label('assessed_assets'),
                func.count(distinct(
                    func.case((Migration.id.is_not(None), Asset.id))
                )).label('migration_planned'),
                func.avg(Assessment.confidence_level).label('avg_confidence'),
                func.sum(Asset.current_monthly_cost).label('total_current_cost'),
                func.avg(Asset.estimated_cloud_cost).label('avg_cloud_cost')
            )
            .select_from(ClientAccount)
            .join(Asset, ClientAccount.id == Asset.client_account_id)
            .outerjoin(Assessment, Asset.id == Assessment.asset_id)
            .outerjoin(Migration, Asset.migration_id == Migration.id)
            .group_by(ClientAccount.id, ClientAccount.company_name)
            .order_by(func.count(Asset.id).desc())
        )
        readiness_dashboard = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "reporting_migration_readiness",
            execution_time,
            len(readiness_dashboard),
            execution_time <= self.thresholds['reporting_query'],
            self.thresholds['reporting_query'],
            f"Migration readiness dashboard: {len(readiness_dashboard)} clients in {execution_time:.3f}s"
        )

    async def _test_bulk_operations(self, session: AsyncSession):
        """Test bulk operation performance."""
        print("📦 Testing Bulk Operation Performance...")

        # Test 1: Bulk asset utilization calculation
        start_time = time.time()
        result = await session.execute(
            select(
                Asset.id,
                Asset.cpu_utilization_percent,
                Asset.memory_utilization_percent,
                func.case(
                    (
                        and_(
                            Asset.cpu_utilization_percent > 80,
                            Asset.memory_utilization_percent > 80
                        ),
                        'High Utilization'
                    ),
                    (
                        or_(
                            Asset.cpu_utilization_percent > 60,
                            Asset.memory_utilization_percent > 60
                        ),
                        'Medium Utilization'
                    ),
                    else_='Low Utilization'
                ).label('utilization_category')
            )
            .where(
                and_(
                    Asset.cpu_utilization_percent.is_not(None),
                    Asset.memory_utilization_percent.is_not(None)
                )
            )
        )
        utilization_calc = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "bulk_utilization_calc",
            execution_time,
            len(utilization_calc),
            execution_time <= self.thresholds['bulk_operation'],
            self.thresholds['bulk_operation'],
            f"Bulk utilization calculation: {len(utilization_calc)} assets in {execution_time:.3f}s"
        )

        # Test 2: Asset cost analysis with window functions
        start_time = time.time()
        result = await session.execute(
            text("""
                SELECT
                    a.id,
                    a.name,
                    a.current_monthly_cost,
                    a.estimated_cloud_cost,
                    AVG(a.current_monthly_cost) OVER (PARTITION BY a.asset_type) as avg_type_cost,
                    RANK() OVER (PARTITION BY ca.id ORDER BY a.current_monthly_cost DESC) as cost_rank_in_client,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a.current_monthly_cost) OVER (PARTITION BY a.asset_type) as median_type_cost
                FROM migration.assets a
                JOIN migration.client_accounts ca ON a.client_account_id = ca.id
                WHERE a.current_monthly_cost IS NOT NULL
                ORDER BY a.current_monthly_cost DESC
                LIMIT 500
            """)
        )
        cost_analysis = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "bulk_cost_analysis",
            execution_time,
            len(cost_analysis),
            execution_time <= self.thresholds['bulk_operation'],
            self.thresholds['bulk_operation'],
            f"Bulk cost analysis: {len(cost_analysis)} assets in {execution_time:.3f}s"
        )

    async def _test_index_performance(self, session: AsyncSession):
        """Test index effectiveness."""
        print("📇 Testing Index Performance...")

        # Test 1: Primary key lookup
        start_time = time.time()
        result = await session.execute(
            select(Asset).where(Asset.id == 1)
        )
        pk_lookup = result.fetchone()
        execution_time = time.time() - start_time

        self._add_result(
            "index_primary_key",
            execution_time,
            1 if pk_lookup else 0,
            execution_time <= 0.1,  # Very fast for PK lookup
            0.1,
            f"Primary key lookup in {execution_time:.3f}s"
        )

        # Test 2: Foreign key join
        start_time = time.time()
        result = await session.execute(
            select(Asset.name, ClientAccount.company_name)
            .join(ClientAccount, Asset.client_account_id == ClientAccount.id)
            .where(ClientAccount.id == 1)
            .limit(100)
        )
        fk_join = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "index_foreign_key",
            execution_time,
            len(fk_join),
            execution_time <= 0.5,
            0.5,
            f"Foreign key join: {len(fk_join)} records in {execution_time:.3f}s"
        )

        # Test 3: Indexed column search (assuming email is indexed)
        start_time = time.time()
        result = await session.execute(
            select(User).where(User.email == 'admin@techcorp.com')
        )
        indexed_search = result.fetchone()
        execution_time = time.time() - start_time

        self._add_result(
            "index_email_search",
            execution_time,
            1 if indexed_search else 0,
            execution_time <= 0.2,
            0.2,
            f"Indexed email search in {execution_time:.3f}s"
        )

    async def _test_memory_usage(self, session: AsyncSession):
        """Test memory usage with large result sets."""
        print("🧠 Testing Memory Usage Performance...")

        # Test 1: Large result set pagination
        start_time = time.time()
        result = await session.execute(
            select(Asset.id, Asset.name, Asset.asset_type)
            .order_by(Asset.id)
            .limit(1000)
        )
        large_result = result.fetchall()
        execution_time = time.time() - start_time

        self._add_result(
            "memory_large_result",
            execution_time,
            len(large_result),
            execution_time <= 3.0,
            3.0,
            f"Large result set: {len(large_result)} records in {execution_time:.3f}s"
        )

        # Test 2: Streaming result simulation
        start_time = time.time()
        result = await session.execute(
            select(Asset.id, Asset.name)
            .order_by(Asset.id)
        )

        # Simulate processing results in batches
        batch_count = 0
        while True:
            batch = result.fetchmany(100)
            if not batch:
                break
            batch_count += 1
            # Simulate processing delay
            await asyncio.sleep(0.001)

        execution_time = time.time() - start_time

        self._add_result(
            "memory_streaming",
            execution_time,
            batch_count * 100,  # Approximate record count
            execution_time <= 5.0,
            5.0,
            f"Streaming processing: {batch_count} batches in {execution_time:.3f}s"
        )

    def _add_result(self, test_name: str, execution_time: float, record_count: int,
                   passed: bool, threshold: float, message: str,
                   details: Optional[Dict[str, Any]] = None):
        """Add a performance test result."""
        result = PerformanceResult(
            test_name=test_name,
            execution_time=execution_time,
            record_count=record_count,
            passed=passed,
            threshold=threshold,
            message=message,
            details=details
        )
        self.results.append(result)

        if self.verbose:
            status = "✅ PASS" if passed else "❌ SLOW"
            print(f"  {status}: {message} (threshold: {threshold}s)")

    def _generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        execution_times = [r.execution_time for r in self.results]
        avg_execution_time = mean(execution_times) if execution_times else 0
        median_execution_time = median(execution_times) if execution_times else 0
        max_execution_time = max(execution_times) if execution_times else 0

        # Categorize results
        categories = {
            'simple': [r for r in self.results if 'simple' in r.test_name],
            'complex': [r for r in self.results if 'complex' in r.test_name],
            'aggregation': [r for r in self.results if 'aggregation' in r.test_name],
            'search': [r for r in self.results if 'search' in r.test_name],
            'reporting': [r for r in self.results if 'reporting' in r.test_name],
            'bulk': [r for r in self.results if 'bulk' in r.test_name],
            'index': [r for r in self.results if 'index' in r.test_name],
            'memory': [r for r in self.results if 'memory' in r.test_name]
        }

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "performance_score": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "avg_execution_time": round(avg_execution_time, 3),
                "median_execution_time": round(median_execution_time, 3),
                "max_execution_time": round(max_execution_time, 3),
                "benchmark_mode": self.benchmark_mode
            },
            "category_performance": {
                name: {
                    "total_tests": len(results),
                    "passed_tests": sum(1 for r in results if r.passed),
                    "avg_execution_time": round(mean([r.execution_time for r in results]), 3) if results else 0,
                    "max_execution_time": round(max([r.execution_time for r in results]), 3) if results else 0
                }
                for name, results in categories.items() if results
            },
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "execution_time": round(r.execution_time, 3),
                    "record_count": r.record_count,
                    "passed": r.passed,
                    "threshold": r.threshold,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.results
            ],
            "performance_assessment": self._assess_performance(),
            "recommendations": self._generate_recommendations()
        }

        return report

    def _assess_performance(self) -> str:
        """Assess overall performance."""
        passed_rate = (sum(1 for r in self.results if r.passed) / len(self.results)) * 100
        avg_time = mean([r.execution_time for r in self.results])

        if passed_rate >= 95 and avg_time < 1.0:
            return "EXCELLENT - Outstanding performance across all tests"
        elif passed_rate >= 90 and avg_time < 2.0:
            return "GOOD - Good performance with minor optimization opportunities"
        elif passed_rate >= 75 and avg_time < 5.0:
            return "ACCEPTABLE - Adequate performance for demo purposes"
        elif passed_rate >= 50:
            return "CONCERNING - Performance issues may impact user experience"
        else:
            return "POOR - Significant performance problems detected"

    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        failed_results = [r for r in self.results if not r.passed]

        if any('simple' in r.test_name for r in failed_results):
            recommendations.append("Consider adding basic indexes on frequently queried columns")

        if any('complex' in r.test_name for r in failed_results):
            recommendations.append("Optimize complex joins - consider query restructuring or additional indexes")

        if any('search' in r.test_name for r in failed_results):
            recommendations.append("Implement full-text search indexes for text search operations")

        if any('reporting' in r.test_name for r in failed_results):
            recommendations.append("Consider implementing materialized views for complex reporting queries")

        if any('bulk' in r.test_name for r in failed_results):
            recommendations.append("Optimize bulk operations - consider batch processing or query optimization")

        if any('memory' in r.test_name for r in failed_results):
            recommendations.append("Implement proper pagination and result streaming for large datasets")

        if not failed_results:
            recommendations.append("Performance is excellent - maintain current optimization level")
            recommendations.append("Consider performance monitoring in production environment")

        return recommendations

def print_performance_report(report: Dict[str, Any]):
    """Print formatted performance report."""
    print("\n" + "="*60)
    print("⚡ PERFORMANCE VALIDATION REPORT")
    print("="*60)

    summary = report['summary']
    print(f"📅 Generated: {report['timestamp']}")
    print(f"🔍 Total Tests: {summary['total_tests']}")
    print(f"✅ Passed: {summary['passed_tests']}")
    print(f"❌ Failed: {summary['failed_tests']}")
    print(f"🏆 Performance Score: {summary['performance_score']:.1f}%")
    print(f"⏱️ Average Time: {summary['avg_execution_time']}s")
    print(f"📊 Median Time: {summary['median_execution_time']}s")
    print(f"⏰ Max Time: {summary['max_execution_time']}s")

    if summary['benchmark_mode']:
        print("🧪 Benchmark Mode: Relaxed thresholds")

    # Performance assessment
    print(f"\n⚡ PERFORMANCE ASSESSMENT: {report['performance_assessment']}")

    # Category breakdown
    if report['category_performance']:
        print("\n📊 PERFORMANCE BY CATEGORY:")
        print("-" * 40)
        for category, stats in report['category_performance'].items():
            pass_rate = (stats['passed_tests'] / stats['total_tests']) * 100
            print(f"{category.upper():12} | {pass_rate:5.1f}% | Avg: {stats['avg_execution_time']:6.3f}s | Max: {stats['max_execution_time']:6.3f}s")

    # Failed tests
    if summary['failed_tests'] > 0:
        print("\n❌ SLOW TESTS:")
        print("-" * 40)
        failed = [r for r in report['detailed_results'] if not r['passed']]
        for result in failed:
            print(f"  • {result['message']}")
            print(f"    Time: {result['execution_time']}s (threshold: {result['threshold']}s)")

    # Recommendations
    if report['recommendations']:
        print("\n💡 PERFORMANCE RECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")

    # Overall status
    if summary['failed_tests'] == 0:
        print("\n🎉 ALL PERFORMANCE TESTS PASSED!")
        print("Database performance is excellent for demo purposes.")
    else:
        print("\n⚠️ PERFORMANCE ISSUES DETECTED")
        print(f"Found {summary['failed_tests']} tests exceeding performance thresholds.")

async def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Validate database performance')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--benchmark', '-b', action='store_true', help='Benchmark mode (relaxed thresholds)')
    parser.add_argument('--export-report', '-e', help='Export report to JSON file')

    args = parser.parse_args()

    validator = PerformanceValidator(verbose=args.verbose, benchmark_mode=args.benchmark)

    try:
        report = await validator.run_performance_tests()

        if args.export_report:
            with open(args.export_report, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Report exported to {args.export_report}")

        print_performance_report(report)

        # Exit with appropriate code
        if report['summary']['failed_tests'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"❌ Performance validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

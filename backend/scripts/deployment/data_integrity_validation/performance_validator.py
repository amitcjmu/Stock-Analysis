"""
Database performance validation for data integrity checking.
Tests query performance and generates monitoring queries.
"""

import logging
import time
from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PerformanceValidator:
    """Validates database performance and generates monitoring queries"""

    def __init__(self, client_account_id: str = None, engagement_id: str = None):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def validate_query_performance(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Test performance of critical queries.

        Returns:
            Dict containing performance validation results
        """
        logger.info("⚡ Validating query performance...")

        results = {
            "valid": True,
            "performance_metrics": {},
            "slow_queries": [],
            "issues": [],
        }

        try:
            # Define critical queries to test
            critical_queries = [
                {
                    "name": "client_account_lookup",
                    "query": "SELECT id, name FROM client_accounts WHERE id = :client_id",
                    "params": {
                        "client_id": self.client_account_id
                        or "11111111-1111-1111-1111-111111111111"
                    },
                    "max_time_ms": 100,
                },
                {
                    "name": "data_import_by_client",
                    "query": """
                        SELECT di.id, di.created_at, di.status, COUNT(rir.id) as record_count
                        FROM data_imports di
                        LEFT JOIN raw_import_records rir ON di.id = rir.data_import_id
                        WHERE di.client_account_id = :client_id
                        GROUP BY di.id, di.created_at, di.status
                        ORDER BY di.created_at DESC
                        LIMIT 10
                    """,
                    "params": {
                        "client_id": self.client_account_id
                        or "11111111-1111-1111-1111-111111111111"
                    },
                    "max_time_ms": 500,
                },
                {
                    "name": "discovery_flows_status",
                    "query": """
                        SELECT df.id, df.flow_id, df.current_phase, df.status
                        FROM discovery_flows df
                        WHERE df.client_account_id = :client_id
                          AND df.status IN ('running', 'paused', 'waiting_for_approval')
                        ORDER BY df.updated_at DESC
                        LIMIT 20
                    """,
                    "params": {
                        "client_id": self.client_account_id
                        or "11111111-1111-1111-1111-111111111111"
                    },
                    "max_time_ms": 300,
                },
                {
                    "name": "crewai_flow_extensions",
                    "query": """
                        SELECT cfse.id, cfse.flow_id, cfse.current_state
                        FROM crewai_flow_state_extensions cfse
                        WHERE cfse.client_account_id = :client_id
                        ORDER BY cfse.updated_at DESC
                        LIMIT 10
                    """,
                    "params": {
                        "client_id": self.client_account_id
                        or "11111111-1111-1111-1111-111111111111"
                    },
                    "max_time_ms": 200,
                },
                {
                    "name": "master_flow_orchestrators",
                    "query": """
                        SELECT mfo.id, mfo.flow_type, mfo.status, mfo.progress_percentage
                        FROM master_flow_orchestrators mfo
                        WHERE mfo.client_account_id = :client_id
                        ORDER BY mfo.updated_at DESC
                        LIMIT 10
                    """,
                    "params": {
                        "client_id": self.client_account_id
                        or "11111111-1111-1111-1111-111111111111"
                    },
                    "max_time_ms": 200,
                },
            ]

            for query_test in critical_queries:
                await self._test_single_query(session, query_test, results)

            # Calculate overall performance score
            total_queries = len(critical_queries)
            slow_queries = len(results["slow_queries"])
            performance_score = (
                (total_queries - slow_queries) / total_queries
                if total_queries > 0
                else 1.0
            )

            results["performance_score"] = performance_score

            if slow_queries > 0:
                results["valid"] = False
                logger.warning(
                    f"⚠️ Found {slow_queries} slow queries out of {total_queries} tested"
                )
            else:
                logger.info("✅ All queries performed within acceptable limits")

        except Exception as e:
            logger.error(
                f"❌ Query performance validation failed: {str(e)}", exc_info=True
            )
            results["valid"] = False
            results["issues"].append(f"Performance validation error: {str(e)}")

        return results

    async def _test_single_query(
        self, session: AsyncSession, query_test: Dict[str, Any], results: Dict[str, Any]
    ):
        """Test performance of a single query"""
        try:
            query_name = query_test["name"]
            query_sql = query_test["query"]
            query_params = query_test.get("params", {})
            max_time_ms = query_test["max_time_ms"]

            # Execute query and measure time
            start_time = time.time()

            result = await session.execute(text(query_sql), query_params)
            rows = result.fetchall()

            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000

            # Record performance metrics
            performance_metric = {
                "query_name": query_name,
                "execution_time_ms": round(execution_time_ms, 2),
                "max_time_ms": max_time_ms,
                "row_count": len(rows),
                "status": "OK" if execution_time_ms <= max_time_ms else "SLOW",
            }

            results["performance_metrics"][query_name] = performance_metric

            if execution_time_ms > max_time_ms:
                results["slow_queries"].append(performance_metric)
                results["issues"].append(
                    f"Slow query {query_name}: {execution_time_ms:.2f}ms > {max_time_ms}ms"
                )
                logger.warning(
                    f"🐌 Slow query {query_name}: {execution_time_ms:.2f}ms (limit: {max_time_ms}ms)"
                )
            else:
                logger.debug(f"⚡ Query {query_name}: {execution_time_ms:.2f}ms (OK)")

        except Exception as e:
            logger.error(
                f"❌ Failed to test query {query_test.get('name', 'unknown')}: {str(e)}"
            )
            results["issues"].append(
                f"Query test failed for {query_test.get('name', 'unknown')}: {str(e)}"
            )

    async def generate_monitoring_queries(self) -> Dict[str, str]:
        """
        Generate monitoring queries for ongoing database health checks.

        Returns:
            Dict of query names to SQL strings for monitoring
        """
        logger.info("📊 Generating monitoring queries...")

        monitoring_queries = {
            "table_row_counts": """
                SELECT
                    'client_accounts' as table_name, COUNT(*) as row_count
                FROM client_accounts
                UNION ALL
                SELECT
                    'data_imports' as table_name, COUNT(*) as row_count
                FROM data_imports
                UNION ALL
                SELECT
                    'raw_import_records' as table_name, COUNT(*) as row_count
                FROM raw_import_records
                UNION ALL
                SELECT
                    'discovery_flows' as table_name, COUNT(*) as row_count
                FROM discovery_flows
                UNION ALL
                SELECT
                    'crewai_flow_state_extensions' as table_name, COUNT(*) as row_count
                FROM crewai_flow_state_extensions
                UNION ALL
                SELECT
                    'master_flow_orchestrators' as table_name, COUNT(*) as row_count
                FROM master_flow_orchestrators
                ORDER BY table_name;
            """,
            "active_flows_by_status": """
                SELECT
                    status,
                    COUNT(*) as count,
                    AVG(progress_percentage) as avg_progress
                FROM discovery_flows
                WHERE status IN ('running', 'paused', 'waiting_for_approval')
                GROUP BY status
                ORDER BY count DESC;
            """,
            "recent_data_imports": """
                SELECT
                    DATE(created_at) as import_date,
                    COUNT(*) as import_count,
                    SUM(record_count) as total_records,
                    AVG(record_count) as avg_records_per_import
                FROM data_imports
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                ORDER BY import_date DESC;
            """,
            "client_account_activity": """
                SELECT
                    ca.name as client_name,
                    COUNT(DISTINCT di.id) as data_imports,
                    COUNT(DISTINCT df.id) as discovery_flows,
                    COUNT(DISTINCT mfo.id) as master_flows,
                    MAX(di.created_at) as last_import,
                    MAX(df.updated_at) as last_flow_update
                FROM client_accounts ca
                LEFT JOIN data_imports di ON ca.id = di.client_account_id
                LEFT JOIN discovery_flows df ON ca.id = df.client_account_id
                LEFT JOIN master_flow_orchestrators mfo ON ca.id = mfo.client_account_id
                GROUP BY ca.id, ca.name
                ORDER BY last_flow_update DESC NULLS LAST
                LIMIT 20;
            """,
            "database_size_analysis": """
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 15;
            """,
            "constraint_violations": """
                SELECT
                    conrelid::regclass as table_name,
                    conname as constraint_name,
                    contype as constraint_type
                FROM pg_constraint
                WHERE NOT convalidated
                ORDER BY conrelid::regclass, conname;
            """,
        }

        # Add client-specific monitoring if client_account_id is provided
        if self.client_account_id:
            monitoring_queries[
                "client_specific_metrics"
            ] = f"""
                SELECT
                    'Data Imports' as metric, COUNT(*) as value
                FROM data_imports
                WHERE client_account_id = '{self.client_account_id}'
                UNION ALL
                SELECT
                    'Discovery Flows' as metric, COUNT(*) as value
                FROM discovery_flows
                WHERE client_account_id = '{self.client_account_id}'
                UNION ALL
                SELECT
                    'Active Flows' as metric, COUNT(*) as value
                FROM discovery_flows
                WHERE client_account_id = '{self.client_account_id}'
                  AND status IN ('running', 'paused', 'waiting_for_approval')
                UNION ALL
                SELECT
                    'Import Records' as metric, COUNT(*) as value
                FROM raw_import_records rir
                JOIN data_imports di ON rir.data_import_id = di.id
                WHERE di.client_account_id = '{self.client_account_id}'
                ORDER BY metric;
            """

        logger.info(f"📊 Generated {len(monitoring_queries)} monitoring queries")
        return monitoring_queries

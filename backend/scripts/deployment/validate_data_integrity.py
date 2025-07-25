#!/usr/bin/env python3
"""
Production Data Integrity Validation Script

This script validates data integrity in production environments by checking:
1. Foreign key relationships are properly established
2. No orphaned records exist
3. Cascade deletion rules are configured correctly
4. Performance monitoring queries execute efficiently
5. Database constraints are enforced

Usage:
    python scripts/deployment/validate_data_integrity.py
    python scripts/deployment/validate_data_integrity.py --client-id <uuid>
    python scripts/deployment/validate_data_integrity.py --engagement-id <uuid>
    python scripts/deployment/validate_data_integrity.py --fix-issues
"""

import argparse
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import text
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


class DataIntegrityValidator:
    """
    Production data integrity validator for the discovery flow system.

    This class provides comprehensive validation of data relationships,
    constraints, and performance characteristics in production environments.
    """

    def __init__(
        self,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        fix_issues: bool = False,
    ):
        """
        Initialize the data integrity validator.

        Args:
            client_account_id: Optional client account ID to limit scope
            engagement_id: Optional engagement ID to limit scope
            fix_issues: Whether to attempt to fix identified issues
        """
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.fix_issues = fix_issues
        self.issues_found = []
        self.performance_metrics = {}

    async def validate_all(self) -> Dict[str, Any]:
        """
        Run complete data integrity validation.

        Returns:
            Dict containing validation results and performance metrics
        """
        logger.info("🔍 Starting comprehensive data integrity validation")

        start_time = datetime.now()
        results = {
            "validation_timestamp": start_time.isoformat(),
            "scope": {
                "client_account_id": self.client_account_id,
                "engagement_id": self.engagement_id,
            },
            "tests": {},
            "issues": [],
            "performance_metrics": {},
            "summary": {},
        }

        async with AsyncSessionLocal() as session:
            try:
                # 1. Validate foreign key relationships
                logger.info("📋 Validating foreign key relationships...")
                fk_results = await self._validate_foreign_key_relationships(session)
                results["tests"]["foreign_key_relationships"] = fk_results

                # 2. Check for orphaned records
                logger.info("🔍 Checking for orphaned records...")
                orphan_results = await self._check_orphaned_records(session)
                results["tests"]["orphaned_records"] = orphan_results

                # 3. Validate cascade deletion configuration
                logger.info("🔗 Validating cascade deletion configuration...")
                cascade_results = await self._validate_cascade_configuration(session)
                results["tests"]["cascade_configuration"] = cascade_results

                # 4. Test constraint enforcement
                logger.info("🛡️ Testing constraint enforcement...")
                constraint_results = await self._test_constraint_enforcement(session)
                results["tests"]["constraint_enforcement"] = constraint_results

                # 5. Validate data consistency
                logger.info("✅ Validating data consistency...")
                consistency_results = await self._validate_data_consistency(session)
                results["tests"]["data_consistency"] = consistency_results

                # 6. Performance validation
                logger.info("⚡ Running performance validation...")
                performance_results = await self._validate_query_performance(session)
                results["tests"]["query_performance"] = performance_results

                # 7. Multi-tenant isolation validation
                logger.info("🏢 Validating multi-tenant isolation...")
                isolation_results = await self._validate_tenant_isolation(session)
                results["tests"]["tenant_isolation"] = isolation_results

                # Compile results
                results["issues"] = self.issues_found
                results["performance_metrics"] = self.performance_metrics

                # Generate summary
                total_tests = len(results["tests"])
                passed_tests = sum(
                    1
                    for test in results["tests"].values()
                    if test.get("status") == "passed"
                )
                failed_tests = total_tests - passed_tests

                results["summary"] = {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "total_issues": len(self.issues_found),
                    "validation_duration_seconds": (
                        datetime.now() - start_time
                    ).total_seconds(),
                    "overall_status": (
                        "passed"
                        if failed_tests == 0 and len(self.issues_found) == 0
                        else "failed"
                    ),
                }

                logger.info(
                    f"✅ Validation completed: {passed_tests}/{total_tests} tests passed, "
                    f"{len(self.issues_found)} issues found"
                )

                return results

            except Exception as e:
                logger.error(f"❌ Validation failed: {e}")
                results["error"] = str(e)
                results["summary"] = {"overall_status": "error"}
                return results

    async def _validate_foreign_key_relationships(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """Validate that all foreign key relationships are properly configured"""
        try:
            start_time = datetime.now()

            # Check for required foreign key constraints
            required_constraints = [
                (
                    "data_imports",
                    "master_flow_id",
                    "crewai_flow_state_extensions",
                    "id",
                ),
                ("discovery_flows", "data_import_id", "data_imports", "id"),
                ("raw_import_records", "data_import_id", "data_imports", "id"),
                (
                    "raw_import_records",
                    "master_flow_id",
                    "crewai_flow_state_extensions",
                    "id",
                ),
                ("assets", "discovery_flow_id", "discovery_flows", "flow_id"),
                ("assets", "master_flow_id", "crewai_flow_state_extensions", "id"),
            ]

            constraint_query = text(
                """
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN (
                    'data_imports', 'discovery_flows', 'raw_import_records', 'assets'
                )
            """
            )

            result = await session.execute(constraint_query)
            existing_constraints = {
                (
                    row.table_name,
                    row.column_name,
                    row.foreign_table_name,
                    row.foreign_column_name,
                )
                for row in result.all()
            }

            missing_constraints = []
            for constraint in required_constraints:
                if constraint not in existing_constraints:
                    missing_constraints.append(constraint)
                    self.issues_found.append(
                        {
                            "type": "missing_foreign_key_constraint",
                            "severity": "high",
                            "description": f"Missing FK constraint: {constraint[0]}.{constraint[1]} -> {constraint[2]}.{constraint[3]}",
                            "table": constraint[0],
                            "column": constraint[1],
                        }
                    )

            execution_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["foreign_key_validation_time"] = execution_time

            return {
                "status": "passed" if len(missing_constraints) == 0 else "failed",
                "execution_time_seconds": execution_time,
                "required_constraints": len(required_constraints),
                "existing_constraints": len(existing_constraints),
                "missing_constraints": missing_constraints,
            }

        except Exception as e:
            logger.error(f"❌ Foreign key validation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _check_orphaned_records(self, session: AsyncSession) -> Dict[str, Any]:
        """Check for orphaned records that violate referential integrity"""
        try:
            start_time = datetime.now()
            orphaned_records = {}

            # Build WHERE clause for scoping
            scope_conditions = []
            params = {}

            if self.client_account_id:
                scope_conditions.append("client_account_id = :client_account_id")
                params["client_account_id"] = self.client_account_id

            if self.engagement_id:
                scope_conditions.append("engagement_id = :engagement_id")
                params["engagement_id"] = self.engagement_id

            scope_where = (
                f"WHERE {' AND '.join(scope_conditions)}" if scope_conditions else ""
            )

            # Check for orphaned discovery flows
            orphan_discovery_query = text(
                f"""
                SELECT COUNT(*) as count
                FROM discovery_flows df
                LEFT JOIN crewai_flow_state_extensions mf ON df.master_flow_id = mf.flow_id
                {scope_where}
                {' AND ' if scope_where else 'WHERE '}mf.flow_id IS NULL
                AND df.master_flow_id IS NOT NULL
            """
            )

            result = await session.execute(orphan_discovery_query, params)
            orphaned_discovery_count = result.scalar() or 0
            orphaned_records["discovery_flows"] = orphaned_discovery_count

            # Check for orphaned data imports
            orphan_import_query = text(
                f"""
                SELECT COUNT(*) as count
                FROM data_imports di
                LEFT JOIN crewai_flow_state_extensions mf ON di.master_flow_id = mf.flow_id
                {scope_where}
                {' AND ' if scope_where else 'WHERE '}mf.flow_id IS NULL
                AND di.master_flow_id IS NOT NULL
            """
            )

            result = await session.execute(orphan_import_query, params)
            orphaned_import_count = result.scalar() or 0
            orphaned_records["data_imports"] = orphaned_import_count

            # Check for orphaned raw records
            orphan_raw_query = text(
                f"""
                SELECT COUNT(*) as count
                FROM raw_import_records rir
                LEFT JOIN data_imports di ON rir.data_import_id = di.id
                {scope_where}
                {' AND ' if scope_where else 'WHERE '}di.id IS NULL
            """
            )

            result = await session.execute(orphan_raw_query, params)
            orphaned_raw_count = result.scalar() or 0
            orphaned_records["raw_import_records"] = orphaned_raw_count

            # Check for orphaned assets
            orphan_asset_query = text(
                f"""
                SELECT COUNT(*) as count
                FROM assets a
                LEFT JOIN discovery_flows df ON a.discovery_flow_id = df.flow_id
                {scope_where}
                {' AND ' if scope_where else 'WHERE '}df.flow_id IS NULL
                AND a.discovery_flow_id IS NOT NULL
            """
            )

            result = await session.execute(orphan_asset_query, params)
            orphaned_asset_count = result.scalar() or 0
            orphaned_records["assets"] = orphaned_asset_count

            # Add issues for any orphaned records found
            total_orphaned = sum(orphaned_records.values())
            if total_orphaned > 0:
                for table, count in orphaned_records.items():
                    if count > 0:
                        self.issues_found.append(
                            {
                                "type": "orphaned_records",
                                "severity": "high",
                                "description": f"Found {count} orphaned records in {table}",
                                "table": table,
                                "count": count,
                            }
                        )

            execution_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["orphan_check_time"] = execution_time

            return {
                "status": "passed" if total_orphaned == 0 else "failed",
                "execution_time_seconds": execution_time,
                "orphaned_records": orphaned_records,
                "total_orphaned": total_orphaned,
            }

        except Exception as e:
            logger.error(f"❌ Orphaned records check failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _validate_cascade_configuration(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """Validate cascade deletion configuration"""
        try:
            start_time = datetime.now()

            # Check cascade rules for critical relationships
            cascade_query = text(
                """
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    rc.delete_rule,
                    rc.update_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN (
                    'data_imports', 'raw_import_records', 'assets'
                )
            """
            )

            result = await session.execute(cascade_query)
            cascade_rules = result.all()

            # Expected cascade configurations
            expected_cascade_rules = {
                ("data_imports", "master_flow_id"): "CASCADE",
                ("raw_import_records", "data_import_id"): "CASCADE",
                ("raw_import_records", "master_flow_id"): "SET NULL",  # or CASCADE
                ("assets", "master_flow_id"): "CASCADE",
            }

            incorrect_cascades = []
            for row in cascade_rules:
                key = (row.table_name, row.column_name)
                if key in expected_cascade_rules:
                    expected_rule = expected_cascade_rules[key]
                    if row.delete_rule not in [expected_rule, "CASCADE", "SET NULL"]:
                        incorrect_cascades.append(
                            {
                                "table": row.table_name,
                                "column": row.column_name,
                                "current_rule": row.delete_rule,
                                "expected_rule": expected_rule,
                            }
                        )

                        self.issues_found.append(
                            {
                                "type": "incorrect_cascade_rule",
                                "severity": "medium",
                                "description": f"Unexpected cascade rule for {row.table_name}.{row.column_name}: {row.delete_rule}",
                                "table": row.table_name,
                                "column": row.column_name,
                                "current_rule": row.delete_rule,
                            }
                        )

            execution_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["cascade_validation_time"] = execution_time

            return {
                "status": "passed" if len(incorrect_cascades) == 0 else "failed",
                "execution_time_seconds": execution_time,
                "cascade_rules_checked": len(cascade_rules),
                "incorrect_cascades": incorrect_cascades,
            }

        except Exception as e:
            logger.error(f"❌ Cascade validation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _test_constraint_enforcement(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """Test that database constraints are properly enforced"""
        try:
            start_time = datetime.now()
            constraint_tests = []

            # Test 1: Try to create data import with invalid master_flow_id
            try:
                invalid_import = DataImport(
                    client_account_id=str(uuid.uuid4()),
                    engagement_id=str(uuid.uuid4()),
                    master_flow_id=str(uuid.uuid4()),  # Non-existent
                    import_name="Constraint Test Import",
                    import_type="test",
                    filename="constraint_test.csv",
                    status="pending",
                    imported_by="test_user",
                )

                session.add(invalid_import)
                await session.commit()

                # If we get here, constraint failed
                constraint_tests.append(
                    {
                        "test": "invalid_master_flow_id",
                        "status": "failed",
                        "description": "Constraint should have prevented invalid master_flow_id",
                    }
                )

                await session.rollback()

            except Exception:
                # This is expected - constraint should prevent this
                constraint_tests.append(
                    {
                        "test": "invalid_master_flow_id",
                        "status": "passed",
                        "description": "Constraint properly rejected invalid master_flow_id",
                    }
                )
                await session.rollback()

            # Test 2: Try to create raw record with invalid data_import_id
            try:
                invalid_raw_record = RawImportRecord(
                    data_import_id=str(uuid.uuid4()),  # Non-existent
                    client_account_id=str(uuid.uuid4()),
                    engagement_id=str(uuid.uuid4()),
                    row_number=1,
                    raw_data={"test": "data"},
                    is_processed=False,
                    is_valid=True,
                )

                session.add(invalid_raw_record)
                await session.commit()

                # If we get here, constraint failed
                constraint_tests.append(
                    {
                        "test": "invalid_data_import_id",
                        "status": "failed",
                        "description": "Constraint should have prevented invalid data_import_id",
                    }
                )

                await session.rollback()

            except Exception:
                # This is expected - constraint should prevent this
                constraint_tests.append(
                    {
                        "test": "invalid_data_import_id",
                        "status": "passed",
                        "description": "Constraint properly rejected invalid data_import_id",
                    }
                )
                await session.rollback()

            failed_tests = [
                test for test in constraint_tests if test["status"] == "failed"
            ]
            if failed_tests:
                for test in failed_tests:
                    self.issues_found.append(
                        {
                            "type": "constraint_enforcement_failure",
                            "severity": "high",
                            "description": test["description"],
                            "test": test["test"],
                        }
                    )

            execution_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["constraint_test_time"] = execution_time

            return {
                "status": "passed" if len(failed_tests) == 0 else "failed",
                "execution_time_seconds": execution_time,
                "tests_run": len(constraint_tests),
                "tests_passed": len(
                    [t for t in constraint_tests if t["status"] == "passed"]
                ),
                "test_results": constraint_tests,
            }

        except Exception as e:
            logger.error(f"❌ Constraint enforcement test failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _validate_data_consistency(self, session: AsyncSession) -> Dict[str, Any]:
        """Validate overall data consistency"""
        try:
            start_time = datetime.now()
            consistency_issues = []

            # Build scope conditions
            scope_conditions = []
            params = {}

            if self.client_account_id:
                scope_conditions.append("mf.client_account_id = :client_account_id")
                params["client_account_id"] = self.client_account_id

            if self.engagement_id:
                scope_conditions.append("mf.engagement_id = :engagement_id")
                params["engagement_id"] = self.engagement_id

            scope_where = (
                f"WHERE {' AND '.join(scope_conditions)}" if scope_conditions else ""
            )

            # Check for discovery flows without corresponding master flows
            consistency_query = text(
                f"""
                SELECT
                    COUNT(CASE WHEN df.master_flow_id IS NOT NULL AND mf.flow_id IS NULL THEN 1 END) as orphaned_discovery_flows,
                    COUNT(CASE WHEN di.master_flow_id IS NOT NULL AND mf2.flow_id IS NULL THEN 1 END) as orphaned_data_imports,
                    COUNT(CASE WHEN df.data_import_id IS NOT NULL AND di2.id IS NULL THEN 1 END) as discovery_flows_missing_imports,
                    COUNT(CASE WHEN rir.asset_id IS NOT NULL AND a.id IS NULL THEN 1 END) as raw_records_missing_assets
                FROM crewai_flow_state_extensions mf
                FULL OUTER JOIN discovery_flows df ON df.master_flow_id = mf.flow_id
                FULL OUTER JOIN crewai_flow_state_extensions mf2 ON mf2.flow_id = mf.flow_id
                FULL OUTER JOIN data_imports di ON di.master_flow_id = mf.flow_id
                FULL OUTER JOIN data_imports di2 ON di2.id = df.data_import_id
                FULL OUTER JOIN raw_import_records rir ON rir.data_import_id = di.id
                FULL OUTER JOIN assets a ON a.id = rir.asset_id
                {scope_where}
            """
            )

            result = await session.execute(consistency_query, params)
            consistency_stats = result.first()

            # Check each consistency metric
            consistency_metrics = {
                "orphaned_discovery_flows": consistency_stats.orphaned_discovery_flows
                or 0,
                "orphaned_data_imports": consistency_stats.orphaned_data_imports or 0,
                "discovery_flows_missing_imports": consistency_stats.discovery_flows_missing_imports
                or 0,
                "raw_records_missing_assets": consistency_stats.raw_records_missing_assets
                or 0,
            }

            for metric, count in consistency_metrics.items():
                if count > 0:
                    consistency_issues.append(metric)
                    self.issues_found.append(
                        {
                            "type": "data_consistency_issue",
                            "severity": "high",
                            "description": f"Data consistency issue: {metric} = {count}",
                            "metric": metric,
                            "count": count,
                        }
                    )

            execution_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["consistency_check_time"] = execution_time

            return {
                "status": "passed" if len(consistency_issues) == 0 else "failed",
                "execution_time_seconds": execution_time,
                "consistency_metrics": consistency_metrics,
                "issues_found": consistency_issues,
            }

        except Exception as e:
            logger.error(f"❌ Data consistency validation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _validate_query_performance(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """Validate that critical queries perform within acceptable limits"""
        try:
            performance_tests = []

            # Build scope conditions
            scope_conditions = []
            params = {}

            if self.client_account_id:
                scope_conditions.append("client_account_id = :client_account_id")
                params["client_account_id"] = self.client_account_id

            if self.engagement_id:
                scope_conditions.append("engagement_id = :engagement_id")
                params["engagement_id"] = self.engagement_id

            scope_where = (
                f"WHERE {' AND '.join(scope_conditions)}" if scope_conditions else ""
            )

            # Test 1: Master flow listing query
            start_time = datetime.now()

            master_flow_query = text(
                f"""
                SELECT COUNT(*) FROM crewai_flow_state_extensions
                {scope_where}
            """
            )

            result = await session.execute(master_flow_query, params)
            master_flow_count = result.scalar()

            master_flow_time = (datetime.now() - start_time).total_seconds()

            performance_tests.append(
                {
                    "test": "master_flow_listing",
                    "execution_time_seconds": master_flow_time,
                    "threshold_seconds": 0.1,
                    "passed": master_flow_time < 0.1,
                    "record_count": master_flow_count,
                }
            )

            # Test 2: Discovery flow with joins query
            start_time = datetime.now()

            discovery_join_query = text(
                f"""
                SELECT df.flow_id, df.flow_name, di.import_name, di.status
                FROM discovery_flows df
                JOIN data_imports di ON df.data_import_id = di.id
                JOIN crewai_flow_state_extensions mf ON df.master_flow_id = mf.flow_id
                {scope_where.replace('client_account_id', 'df.client_account_id').replace('engagement_id', 'df.engagement_id') if scope_where else ''}
                LIMIT 100
            """
            )

            result = await session.execute(discovery_join_query, params)
            discovery_results = result.all()

            discovery_join_time = (datetime.now() - start_time).total_seconds()

            performance_tests.append(
                {
                    "test": "discovery_flow_joins",
                    "execution_time_seconds": discovery_join_time,
                    "threshold_seconds": 0.2,
                    "passed": discovery_join_time < 0.2,
                    "record_count": len(discovery_results),
                }
            )

            # Test 3: Asset aggregation query
            start_time = datetime.now()

            asset_aggregation_query = text(
                f"""
                SELECT
                    COUNT(*) as total_assets,
                    AVG(migration_readiness_score) as avg_readiness_score,
                    COUNT(CASE WHEN migration_readiness_score >= 0.8 THEN 1 END) as high_readiness_count
                FROM assets a
                JOIN discovery_flows df ON a.discovery_flow_id = df.flow_id
                {scope_where.replace('client_account_id', 'a.client_account_id').replace('engagement_id', 'a.engagement_id') if scope_where else ''}
            """
            )

            result = await session.execute(asset_aggregation_query, params)
            asset_stats = result.first()

            asset_aggregation_time = (datetime.now() - start_time).total_seconds()

            performance_tests.append(
                {
                    "test": "asset_aggregation",
                    "execution_time_seconds": asset_aggregation_time,
                    "threshold_seconds": 0.3,
                    "passed": asset_aggregation_time < 0.3,
                    "record_count": asset_stats.total_assets if asset_stats else 0,
                }
            )

            # Check for failed performance tests
            failed_performance_tests = [
                test for test in performance_tests if not test["passed"]
            ]
            if failed_performance_tests:
                for test in failed_performance_tests:
                    self.issues_found.append(
                        {
                            "type": "performance_issue",
                            "severity": "medium",
                            "description": f"Query {test['test']} took {test['execution_time_seconds']:.3f}s (threshold: {test['threshold_seconds']}s)",
                            "test": test["test"],
                            "execution_time": test["execution_time_seconds"],
                            "threshold": test["threshold_seconds"],
                        }
                    )

            # Store performance metrics
            for test in performance_tests:
                self.performance_metrics[f"{test['test']}_time"] = test[
                    "execution_time_seconds"
                ]

            return {
                "status": "passed" if len(failed_performance_tests) == 0 else "failed",
                "tests_run": len(performance_tests),
                "tests_passed": len([t for t in performance_tests if t["passed"]]),
                "performance_tests": performance_tests,
            }

        except Exception as e:
            logger.error(f"❌ Query performance validation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _validate_tenant_isolation(self, session: AsyncSession) -> Dict[str, Any]:
        """Validate multi-tenant data isolation"""
        try:
            start_time = datetime.now()
            isolation_tests = []

            # Test 1: Verify all records have proper tenant IDs
            tenant_id_query = text(
                """
                SELECT
                    'crewai_flow_state_extensions' as table_name,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN client_account_id IS NULL THEN 1 END) as missing_client_id,
                    COUNT(CASE WHEN engagement_id IS NULL THEN 1 END) as missing_engagement_id
                FROM crewai_flow_state_extensions

                UNION ALL

                SELECT
                    'discovery_flows' as table_name,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN client_account_id IS NULL THEN 1 END) as missing_client_id,
                    COUNT(CASE WHEN engagement_id IS NULL THEN 1 END) as missing_engagement_id
                FROM discovery_flows

                UNION ALL

                SELECT
                    'data_imports' as table_name,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN client_account_id IS NULL THEN 1 END) as missing_client_id,
                    COUNT(CASE WHEN engagement_id IS NULL THEN 1 END) as missing_engagement_id
                FROM data_imports

                UNION ALL

                SELECT
                    'assets' as table_name,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN client_account_id IS NULL THEN 1 END) as missing_client_id,
                    COUNT(CASE WHEN engagement_id IS NULL THEN 1 END) as missing_engagement_id
                FROM assets
            """
            )

            result = await session.execute(tenant_id_query)
            tenant_results = result.all()

            tenant_violations = []
            for row in tenant_results:
                if row.missing_client_id > 0 or row.missing_engagement_id > 0:
                    tenant_violations.append(
                        {
                            "table": row.table_name,
                            "total_records": row.total_records,
                            "missing_client_id": row.missing_client_id,
                            "missing_engagement_id": row.missing_engagement_id,
                        }
                    )

                    self.issues_found.append(
                        {
                            "type": "tenant_isolation_violation",
                            "severity": "high",
                            "description": f"Table {row.table_name} has records missing tenant IDs: "
                            f"client_id={row.missing_client_id}, engagement_id={row.missing_engagement_id}",
                            "table": row.table_name,
                            "missing_client_id": row.missing_client_id,
                            "missing_engagement_id": row.missing_engagement_id,
                        }
                    )

            isolation_tests.append(
                {
                    "test": "tenant_id_completeness",
                    "status": "passed" if len(tenant_violations) == 0 else "failed",
                    "violations": tenant_violations,
                }
            )

            # Test 2: Check for cross-tenant data leakage
            if self.client_account_id:
                cross_tenant_query = text(
                    """
                    SELECT
                        COUNT(CASE WHEN df.client_account_id != di.client_account_id THEN 1 END) as discovery_import_mismatch,
                        COUNT(CASE WHEN a.client_account_id != df.client_account_id THEN 1 END) as asset_discovery_mismatch,
                        COUNT(CASE WHEN rir.client_account_id != di.client_account_id THEN 1 END) as raw_import_mismatch
                    FROM discovery_flows df
                    LEFT JOIN data_imports di ON df.data_import_id = di.id
                    LEFT JOIN assets a ON a.discovery_flow_id = df.flow_id
                    LEFT JOIN raw_import_records rir ON rir.data_import_id = di.id
                    WHERE df.client_account_id = :client_account_id
                """
                )

                result = await session.execute(
                    cross_tenant_query, {"client_account_id": self.client_account_id}
                )
                cross_tenant_stats = result.first()

                cross_tenant_issues = []
                if cross_tenant_stats.discovery_import_mismatch > 0:
                    cross_tenant_issues.append("discovery_import_mismatch")
                if cross_tenant_stats.asset_discovery_mismatch > 0:
                    cross_tenant_issues.append("asset_discovery_mismatch")
                if cross_tenant_stats.raw_import_mismatch > 0:
                    cross_tenant_issues.append("raw_import_mismatch")

                if cross_tenant_issues:
                    for issue in cross_tenant_issues:
                        self.issues_found.append(
                            {
                                "type": "cross_tenant_data_leakage",
                                "severity": "critical",
                                "description": f"Cross-tenant data leakage detected: {issue}",
                                "issue": issue,
                            }
                        )

                isolation_tests.append(
                    {
                        "test": "cross_tenant_leakage_check",
                        "status": (
                            "passed" if len(cross_tenant_issues) == 0 else "failed"
                        ),
                        "issues": cross_tenant_issues,
                    }
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["tenant_isolation_time"] = execution_time

            failed_tests = [
                test for test in isolation_tests if test["status"] == "failed"
            ]

            return {
                "status": "passed" if len(failed_tests) == 0 else "failed",
                "execution_time_seconds": execution_time,
                "tests_run": len(isolation_tests),
                "tests_passed": len(
                    [t for t in isolation_tests if t["status"] == "passed"]
                ),
                "isolation_tests": isolation_tests,
            }

        except Exception as e:
            logger.error(f"❌ Tenant isolation validation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def generate_monitoring_queries(self) -> Dict[str, str]:
        """Generate SQL queries for ongoing monitoring"""
        return {
            "orphaned_records_check": """
                SELECT
                    'discovery_flows' as table_name,
                    COUNT(*) as orphaned_count
                FROM discovery_flows df
                LEFT JOIN crewai_flow_state_extensions mf ON df.master_flow_id = mf.flow_id
                WHERE mf.flow_id IS NULL AND df.master_flow_id IS NOT NULL

                UNION ALL

                SELECT
                    'data_imports' as table_name,
                    COUNT(*) as orphaned_count
                FROM data_imports di
                LEFT JOIN crewai_flow_state_extensions mf ON di.master_flow_id = mf.flow_id
                WHERE mf.flow_id IS NULL AND di.master_flow_id IS NOT NULL

                UNION ALL

                SELECT
                    'raw_import_records' as table_name,
                    COUNT(*) as orphaned_count
                FROM raw_import_records rir
                LEFT JOIN data_imports di ON rir.data_import_id = di.id
                WHERE di.id IS NULL

                UNION ALL

                SELECT
                    'assets' as table_name,
                    COUNT(*) as orphaned_count
                FROM assets a
                LEFT JOIN discovery_flows df ON a.discovery_flow_id = df.flow_id
                WHERE df.flow_id IS NULL AND a.discovery_flow_id IS NOT NULL;
            """,
            "data_integrity_summary": """
                SELECT
                    COUNT(DISTINCT mf.flow_id) as total_master_flows,
                    COUNT(DISTINCT df.flow_id) as total_discovery_flows,
                    COUNT(DISTINCT di.id) as total_data_imports,
                    COUNT(DISTINCT rir.id) as total_raw_records,
                    COUNT(DISTINCT a.id) as total_assets,
                    COUNT(DISTINCT CASE WHEN df.master_flow_id = mf.flow_id THEN df.flow_id END) as linked_discovery_flows,
                    COUNT(DISTINCT CASE WHEN di.master_flow_id = mf.flow_id THEN di.id END) as linked_data_imports,
                    COUNT(DISTINCT CASE WHEN a.master_flow_id = mf.flow_id THEN a.id END) as linked_assets
                FROM crewai_flow_state_extensions mf
                FULL OUTER JOIN discovery_flows df ON df.master_flow_id = mf.flow_id
                FULL OUTER JOIN data_imports di ON di.master_flow_id = mf.flow_id
                FULL OUTER JOIN raw_import_records rir ON rir.master_flow_id = mf.flow_id
                FULL OUTER JOIN assets a ON a.master_flow_id = mf.flow_id;
            """,
            "performance_metrics": """
                SELECT
                    mf.flow_type,
                    COUNT(*) as flow_count,
                    AVG(EXTRACT(EPOCH FROM (mf.updated_at - mf.created_at))) as avg_duration_seconds,
                    COUNT(CASE WHEN mf.flow_status = 'completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN mf.flow_status = 'failed' THEN 1 END) as failed_count,
                    COUNT(CASE WHEN mf.flow_status = 'active' THEN 1 END) as active_count
                FROM crewai_flow_state_extensions mf
                WHERE mf.created_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY mf.flow_type;
            """,
            "tenant_isolation_check": """
                SELECT
                    table_name,
                    total_records,
                    missing_client_id,
                    missing_engagement_id
                FROM (
                    SELECT
                        'crewai_flow_state_extensions' as table_name,
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN client_account_id IS NULL THEN 1 END) as missing_client_id,
                        COUNT(CASE WHEN engagement_id IS NULL THEN 1 END) as missing_engagement_id
                    FROM crewai_flow_state_extensions

                    UNION ALL

                    SELECT
                        'discovery_flows' as table_name,
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN client_account_id IS NULL THEN 1 END) as missing_client_id,
                        COUNT(CASE WHEN engagement_id IS NULL THEN 1 END) as missing_engagement_id
                    FROM discovery_flows

                    UNION ALL

                    SELECT
                        'data_imports' as table_name,
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN client_account_id IS NULL THEN 1 END) as missing_client_id,
                        COUNT(CASE WHEN engagement_id IS NULL THEN 1 END) as missing_engagement_id
                    FROM data_imports

                    UNION ALL

                    SELECT
                        'assets' as table_name,
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN client_account_id IS NULL THEN 1 END) as missing_client_id,
                        COUNT(CASE WHEN engagement_id IS NULL THEN 1 END) as missing_engagement_id
                    FROM assets
                ) tenant_stats
                WHERE missing_client_id > 0 OR missing_engagement_id > 0;
            """,
        }


async def main():
    """Main function for running data integrity validation"""
    parser = argparse.ArgumentParser(
        description="Validate discovery flow data integrity"
    )
    parser.add_argument(
        "--client-id", help="Limit validation to specific client account ID"
    )
    parser.add_argument(
        "--engagement-id", help="Limit validation to specific engagement ID"
    )
    parser.add_argument(
        "--fix-issues", action="store_true", help="Attempt to fix identified issues"
    )
    parser.add_argument("--output", help="Output file for validation results (JSON)")
    parser.add_argument(
        "--monitoring-queries", action="store_true", help="Generate monitoring queries"
    )

    args = parser.parse_args()

    # Initialize validator
    validator = DataIntegrityValidator(
        client_account_id=args.client_id,
        engagement_id=args.engagement_id,
        fix_issues=args.fix_issues,
    )

    try:
        # Run validation
        logger.info("🚀 Starting data integrity validation...")
        results = await validator.validate_all()

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"📄 Results saved to {args.output}")
        else:
            print(json.dumps(results, indent=2, default=str))

        # Generate monitoring queries if requested
        if args.monitoring_queries:
            monitoring_queries = await validator.generate_monitoring_queries()
            monitoring_file = (
                args.output.replace(".json", "_monitoring.sql")
                if args.output
                else "monitoring_queries.sql"
            )

            with open(monitoring_file, "w") as f:
                f.write("-- Data Integrity Monitoring Queries\n")
                f.write(f"-- Generated on {datetime.now().isoformat()}\n\n")

                for query_name, query_sql in monitoring_queries.items():
                    f.write(f"-- {query_name.replace('_', ' ').title()}\n")
                    f.write(f"{query_sql}\n\n")

            logger.info(f"📊 Monitoring queries saved to {monitoring_file}")

        # Exit with appropriate code
        if results["summary"]["overall_status"] == "passed":
            logger.info("✅ All data integrity validations passed")
            exit(0)
        else:
            logger.error("❌ Data integrity validation failed")
            exit(1)

    except Exception as e:
        logger.error(f"❌ Validation script failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())

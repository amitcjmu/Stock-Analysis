"""
Tenant isolation validation for multi-tenant data security.
Validates that data is properly isolated between different client accounts.
"""

import logging
from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TenantIsolationValidator:
    """Validates multi-tenant data isolation and security"""

    def __init__(self, client_account_id: str = None, engagement_id: str = None):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def validate_tenant_isolation(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Validate that tenant data isolation is properly maintained.

        Returns:
            Dict containing tenant isolation validation results
        """
        logger.info("🏢 Validating tenant isolation...")

        results = {
            "valid": True,
            "isolation_tests": [],
            "cross_tenant_leaks": [],
            "issues": [],
        }

        try:
            # Get list of client accounts to test isolation
            client_accounts_query = text(
                """
                SELECT id, name
                FROM client_accounts
                ORDER BY created_at DESC
                LIMIT 10
            """
            )

            client_result = await session.execute(client_accounts_query)
            client_accounts = [
                {"id": str(row.id), "name": row.name}
                for row in client_result.fetchall()
            ]

            if len(client_accounts) < 2:
                logger.warning(
                    "⚠️ Less than 2 client accounts found - limited tenant isolation testing"
                )
                results["issues"].append(
                    "Insufficient client accounts for comprehensive tenant isolation testing"
                )

            # Test isolation for each major entity type
            entity_tests = [
                {
                    "entity": "data_imports",
                    "description": "Data imports should be isolated by client_account_id",
                },
                {
                    "entity": "raw_import_records",
                    "description": "Import records should only be accessible via their data_import's client",
                },
                {
                    "entity": "discovery_flows",
                    "description": "Discovery flows should be isolated by client_account_id",
                },
                {
                    "entity": "crewai_flow_state_extensions",
                    "description": "CrewAI flow states should be isolated by client_account_id",
                },
                {
                    "entity": "master_flow_orchestrators",
                    "description": "Master flow orchestrators should be isolated by client_account_id",
                },
            ]

            for test in entity_tests:
                await self._test_entity_isolation(
                    session, test, client_accounts, results
                )

            # Test for cross-tenant data leakage
            await self._test_cross_tenant_access(session, client_accounts, results)

            if results["cross_tenant_leaks"]:
                results["valid"] = False
                logger.error(
                    f"❌ Found {len(results['cross_tenant_leaks'])} tenant isolation violations"
                )
            else:
                logger.info("✅ Tenant isolation is properly maintained")

        except Exception as e:
            logger.error(
                f"❌ Tenant isolation validation failed: {str(e)}", exc_info=True
            )
            results["valid"] = False
            results["issues"].append(f"Tenant isolation validation error: {str(e)}")

        return results

    async def _test_entity_isolation(
        self,
        session: AsyncSession,
        test: Dict[str, str],
        client_accounts: list,
        results: Dict[str, Any],
    ):
        """Test isolation for a specific entity type"""
        try:
            entity_name = test["entity"]

            # Check if entity has client_account_id field
            schema_query = text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table_name
                  AND column_name = 'client_account_id'
            """
            )

            schema_result = await session.execute(
                schema_query, {"table_name": entity_name}
            )
            has_client_field = schema_result.fetchone() is not None

            test_result = {
                "entity": entity_name,
                "description": test["description"],
                "has_client_field": has_client_field,
                "isolation_verified": False,
                "cross_tenant_records": 0,
            }

            if has_client_field:
                # Test that records are properly associated with client accounts
                # Note: entity_name is from controlled configuration, not user input
                isolation_query_sql = f"""
                    SELECT
                        client_account_id,
                        COUNT(*) as record_count
                    FROM {entity_name}
                    WHERE client_account_id IS NOT NULL
                    GROUP BY client_account_id
                    ORDER BY record_count DESC
                    LIMIT 20
                """

                isolation_query = text(isolation_query_sql)
                isolation_result = await session.execute(isolation_query)
                client_distribution = [
                    {
                        "client_id": str(row.client_account_id),
                        "record_count": row.record_count,
                    }
                    for row in isolation_result.fetchall()
                ]

                test_result["client_distribution"] = client_distribution
                test_result["isolation_verified"] = len(client_distribution) > 0

                # Check for records without client_account_id (potential isolation breach)
                # Note: entity_name is from controlled configuration, not user input
                orphan_query_sql = f"""
                    SELECT COUNT(*) as orphan_count
                    FROM {entity_name}
                    WHERE client_account_id IS NULL
                """

                orphan_query = text(orphan_query_sql)
                orphan_result = await session.execute(orphan_query)
                orphan_count = (
                    orphan_result.fetchone().orphan_count
                    if orphan_result.fetchone()
                    else 0
                )

                test_result["orphan_records"] = orphan_count

                if orphan_count > 0:
                    results["issues"].append(
                        f"Found {orphan_count} records in {entity_name} without client_account_id"
                    )
                    logger.warning(
                        f"⚠️ Found {orphan_count} orphan records in {entity_name}"
                    )

            else:
                test_result["isolation_verified"] = False
                results["issues"].append(
                    f"Entity {entity_name} does not have client_account_id field for tenant isolation"
                )
                logger.warning(f"⚠️ Entity {entity_name} lacks tenant isolation field")

            results["isolation_tests"].append(test_result)

        except Exception as e:
            logger.error(f"❌ Failed to test isolation for {test['entity']}: {str(e)}")
            results["issues"].append(
                f"Failed to test isolation for {test['entity']}: {str(e)}"
            )

    async def _test_cross_tenant_access(
        self, session: AsyncSession, client_accounts: list, results: Dict[str, Any]
    ):
        """Test for potential cross-tenant data access vulnerabilities"""
        if len(client_accounts) < 2:
            return

        try:
            # Test 1: Check for shared resources between tenants
            shared_resources_query = text(
                """
                SELECT
                    'data_imports' as entity_type,
                    client_account_id,
                    COUNT(*) as count
                FROM data_imports
                GROUP BY client_account_id
                HAVING COUNT(*) > 0

                UNION ALL

                SELECT
                    'discovery_flows' as entity_type,
                    client_account_id,
                    COUNT(*) as count
                FROM discovery_flows
                GROUP BY client_account_id
                HAVING COUNT(*) > 0

                ORDER BY entity_type, client_account_id
            """
            )

            shared_result = await session.execute(shared_resources_query)
            resource_distribution = [
                {
                    "entity_type": row.entity_type,
                    "client_account_id": str(row.client_account_id),
                    "count": row.count,
                }
                for row in shared_result.fetchall()
            ]

            # Test 2: Check for potential foreign key leaks across tenants
            # This would happen if child records reference parents from different tenants
            fk_leak_query = text(
                """
                SELECT
                    rir.id as child_id,
                    rir.data_import_id as child_fk,
                    di.client_account_id as parent_client,
                    'raw_import_records -> data_imports' as relationship
                FROM raw_import_records rir
                JOIN data_imports di ON rir.data_import_id = di.id
                JOIN data_imports di2 ON di2.client_account_id != di.client_account_id
                LIMIT 10
            """
            )

            fk_leak_result = await session.execute(fk_leak_query)
            potential_leaks = [
                {
                    "child_id": str(row.child_id),
                    "parent_client": str(row.parent_client),
                    "relationship": row.relationship,
                }
                for row in fk_leak_result.fetchall()
            ]

            if potential_leaks:
                results["cross_tenant_leaks"].extend(potential_leaks)
                results["issues"].append(
                    f"Found {len(potential_leaks)} potential cross-tenant foreign key references"
                )
                logger.error(
                    f"❌ Found {len(potential_leaks)} cross-tenant foreign key leaks"
                )

            # Test 3: Verify no shared user access across tenants
            # (This would require user-tenant mapping table which may not exist)

            results["resource_distribution"] = resource_distribution

        except Exception as e:
            logger.error(f"❌ Cross-tenant access testing failed: {str(e)}")
            results["issues"].append(f"Cross-tenant access testing failed: {str(e)}")

"""
Foreign key relationship validation for data integrity checking.
Validates that foreign key relationships are properly established.
"""

import logging
from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ForeignKeyValidator:
    """Validates foreign key relationships across the database"""

    def __init__(self, client_account_id: str = None, engagement_id: str = None):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def validate_foreign_key_relationships(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Validate foreign key relationships across the database.

        Returns:
            Dict containing foreign key validation results
        """
        logger.info("🔗 Validating foreign key relationships...")

        results = {
            "valid": True,
            "issues": [],
            "relationships_checked": 0,
            "broken_relationships": [],
        }

        try:
            # Define critical foreign key relationships to validate
            relationships = [
                {
                    "name": "data_import_to_client_account",
                    "parent_table": "client_accounts",
                    "parent_id": "id",
                    "child_table": "data_imports",
                    "child_fk": "client_account_id",
                },
                {
                    "name": "raw_import_record_to_data_import",
                    "parent_table": "data_imports",
                    "parent_id": "id",
                    "child_table": "raw_import_records",
                    "child_fk": "data_import_id",
                },
                {
                    "name": "discovery_flow_to_client_account",
                    "parent_table": "client_accounts",
                    "parent_id": "id",
                    "child_table": "discovery_flows",
                    "child_fk": "client_account_id",
                },
                {
                    "name": "crewai_flow_state_to_client_account",
                    "parent_table": "client_accounts",
                    "parent_id": "id",
                    "child_table": "crewai_flow_state_extensions",
                    "child_fk": "client_account_id",
                },
                {
                    "name": "master_flow_orchestrator_to_client_account",
                    "parent_table": "client_accounts",
                    "parent_id": "id",
                    "child_table": "master_flow_orchestrators",
                    "child_fk": "client_account_id",
                },
            ]

            for relationship in relationships:
                await self._validate_single_relationship(session, relationship, results)

            results["relationships_checked"] = len(relationships)

            if results["broken_relationships"]:
                results["valid"] = False
                logger.error(
                    f"❌ Found {len(results['broken_relationships'])} broken foreign key relationships"
                )
            else:
                logger.info("✅ All foreign key relationships are valid")

        except Exception as e:
            logger.error(f"❌ Foreign key validation failed: {str(e)}", exc_info=True)
            results["valid"] = False
            results["issues"].append(f"Validation error: {str(e)}")

        return results

    async def _validate_single_relationship(
        self,
        session: AsyncSession,
        relationship: Dict[str, str],
        results: Dict[str, Any],
    ):
        """Validate a single foreign key relationship"""
        try:
            # Build query to find orphaned records
            where_clause = ""
            if self.client_account_id:
                where_clause = f" AND c.client_account_id = '{self.client_account_id}'"
            if self.engagement_id:
                where_clause += f" AND c.engagement_id = '{self.engagement_id}'"

            query = text(
                f"""
                SELECT c.{relationship['child_fk']} as orphaned_fk, COUNT(*) as count
                FROM {relationship['child_table']} c
                LEFT JOIN {relationship['parent_table']} p
                    ON c.{relationship['child_fk']} = p.{relationship['parent_id']}
                WHERE p.{relationship['parent_id']} IS NULL
                  AND c.{relationship['child_fk']} IS NOT NULL
                  {where_clause}
                GROUP BY c.{relationship['child_fk']}
                LIMIT 100
            """
            )

            result = await session.execute(query)
            orphaned_records = result.fetchall()

            if orphaned_records:
                broken_relationship = {
                    "relationship_name": relationship["name"],
                    "parent_table": relationship["parent_table"],
                    "child_table": relationship["child_table"],
                    "orphaned_count": len(orphaned_records),
                    "orphaned_foreign_keys": [
                        {"fk_value": str(row.orphaned_fk), "count": row.count}
                        for row in orphaned_records[:10]  # Limit to first 10
                    ],
                }
                results["broken_relationships"].append(broken_relationship)
                results["issues"].append(
                    f"Broken relationship {relationship['name']}: "
                    f"{len(orphaned_records)} orphaned records in {relationship['child_table']}"
                )
                logger.warning(
                    f"⚠️ Found {len(orphaned_records)} orphaned records in {relationship['name']}"
                )
            else:
                logger.debug(f"✅ Relationship {relationship['name']} is valid")

        except Exception as e:
            logger.error(
                f"❌ Failed to validate relationship {relationship['name']}: {str(e)}"
            )
            results["issues"].append(
                f"Failed to validate {relationship['name']}: {str(e)}"
            )

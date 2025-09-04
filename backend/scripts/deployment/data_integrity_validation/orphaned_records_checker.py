"""
Orphaned records detection and reporting for data integrity validation.
Identifies records that should have been deleted but remain in the database.
"""

import logging
from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class OrphanedRecordsChecker:
    """Detects and reports orphaned records in the database"""

    def __init__(
        self,
        client_account_id: str = None,
        engagement_id: str = None,
        fix_issues: bool = False,
    ):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.fix_issues = fix_issues

    async def check_orphaned_records(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Check for orphaned records that should have been cascade deleted.

        Returns:
            Dict containing orphaned records analysis
        """
        logger.info("🔍 Checking for orphaned records...")

        results = {
            "valid": True,
            "orphaned_tables": [],
            "total_orphaned_records": 0,
            "cleaned_records": 0,
            "issues": [],
        }

        try:
            # Define tables to check for orphaned records
            orphan_checks = [
                {
                    "table": "raw_import_records",
                    "parent_table": "data_imports",
                    "foreign_key": "data_import_id",
                    "description": "Import records without parent data_import",
                },
                {
                    "table": "discovery_flows",
                    "parent_table": "client_accounts",
                    "foreign_key": "client_account_id",
                    "description": "Discovery flows without valid client account",
                },
                {
                    "table": "crewai_flow_state_extensions",
                    "parent_table": "client_accounts",
                    "foreign_key": "client_account_id",
                    "description": "CrewAI flow states without valid client account",
                },
                {
                    "table": "master_flow_orchestrators",
                    "parent_table": "client_accounts",
                    "foreign_key": "client_account_id",
                    "description": "Master flow orchestrators without valid client account",
                },
            ]

            for check in orphan_checks:
                await self._check_single_table(session, check, results)

            if results["total_orphaned_records"] > 0:
                results["valid"] = False
                logger.error(
                    f"❌ Found {results['total_orphaned_records']} total orphaned records"
                )
            else:
                logger.info("✅ No orphaned records found")

        except Exception as e:
            logger.error(f"❌ Orphaned records check failed: {str(e)}", exc_info=True)
            results["valid"] = False
            results["issues"].append(f"Check failed: {str(e)}")

        return results

    async def _check_single_table(
        self, session: AsyncSession, check: Dict[str, str], results: Dict[str, Any]
    ):
        """Check a single table for orphaned records"""
        try:
            # Build scope filter
            scope_filter = ""
            if self.client_account_id:
                scope_filter = f" AND o.client_account_id = '{self.client_account_id}'"
            if self.engagement_id:
                scope_filter += f" AND o.engagement_id = '{self.engagement_id}'"

            # Query to find orphaned records
            query = text(
                f"""
                SELECT COUNT(*) as orphaned_count
                FROM {check['table']} o
                LEFT JOIN {check['parent_table']} p ON o.{check['foreign_key']} = p.id
                WHERE p.id IS NULL
                  AND o.{check['foreign_key']} IS NOT NULL
                  {scope_filter}
            """
            )

            result = await session.execute(query)
            count_row = result.fetchone()
            orphaned_count = count_row.orphaned_count if count_row else 0

            if orphaned_count > 0:
                # Get sample of orphaned records for analysis
                sample_query = text(
                    f"""
                    SELECT o.id, o.{check['foreign_key']}, o.created_at
                    FROM {check['table']} o
                    LEFT JOIN {check['parent_table']} p ON o.{check['foreign_key']} = p.id
                    WHERE p.id IS NULL
                      AND o.{check['foreign_key']} IS NOT NULL
                      {scope_filter}
                    ORDER BY o.created_at DESC
                    LIMIT 10
                """
                )

                sample_result = await session.execute(sample_query)
                sample_records = [
                    {
                        "id": str(row.id),
                        "foreign_key_value": str(row[1]),  # foreign key value
                        "created_at": (
                            row.created_at.isoformat() if row.created_at else None
                        ),
                    }
                    for row in sample_result.fetchall()
                ]

                orphaned_table = {
                    "table_name": check["table"],
                    "description": check["description"],
                    "parent_table": check["parent_table"],
                    "foreign_key": check["foreign_key"],
                    "orphaned_count": orphaned_count,
                    "sample_records": sample_records,
                }

                results["orphaned_tables"].append(orphaned_table)
                results["total_orphaned_records"] += orphaned_count
                results["issues"].append(
                    f"Found {orphaned_count} orphaned records in {check['table']}: {check['description']}"
                )

                logger.warning(
                    f"⚠️ Found {orphaned_count} orphaned records in {check['table']}"
                )

                # Attempt to fix if requested
                if self.fix_issues:
                    cleaned_count = await self._clean_orphaned_records(
                        session, check, scope_filter
                    )
                    results["cleaned_records"] += cleaned_count
                    orphaned_table["cleaned_count"] = cleaned_count

            else:
                logger.debug(f"✅ No orphaned records found in {check['table']}")

        except Exception as e:
            logger.error(
                f"❌ Failed to check {check['table']} for orphaned records: {str(e)}"
            )
            results["issues"].append(f"Failed to check {check['table']}: {str(e)}")

    async def _clean_orphaned_records(
        self, session: AsyncSession, check: Dict[str, str], scope_filter: str
    ) -> int:
        """Clean orphaned records if fix_issues is enabled"""
        if not self.fix_issues:
            return 0

        try:
            logger.info(
                f"🧹 Attempting to clean orphaned records from {check['table']}"
            )

            # Delete orphaned records
            delete_query = text(
                f"""
                DELETE FROM {check['table']}
                WHERE id IN (
                    SELECT o.id
                    FROM {check['table']} o
                    LEFT JOIN {check['parent_table']} p ON o.{check['foreign_key']} = p.id
                    WHERE p.id IS NULL
                      AND o.{check['foreign_key']} IS NOT NULL
                      {scope_filter}
                    LIMIT 1000  -- Limit batch size for safety
                )
            """
            )

            result = await session.execute(delete_query)
            cleaned_count = result.rowcount

            if cleaned_count > 0:
                logger.info(
                    f"🧹 Cleaned {cleaned_count} orphaned records from {check['table']}"
                )
                await session.commit()

            return cleaned_count

        except Exception as e:
            logger.error(
                f"❌ Failed to clean orphaned records from {check['table']}: {str(e)}"
            )
            await session.rollback()
            return 0

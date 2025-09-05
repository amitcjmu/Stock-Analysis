"""
Database constraint validation and cascade configuration testing.
Validates that database constraints are properly enforced and configured.
"""

import logging
import uuid
from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ConstraintValidator:
    """Validates database constraints and cascade configurations"""

    def __init__(
        self,
        client_account_id: str = None,
        engagement_id: str = None,
        fix_issues: bool = False,
    ):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.fix_issues = fix_issues

    async def validate_cascade_configuration(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Validate that cascade deletion rules are configured correctly.

        Returns:
            Dict containing cascade configuration validation results
        """
        logger.info("🔗 Validating cascade deletion configuration...")

        results = {
            "valid": True,
            "cascade_rules": [],
            "missing_cascades": [],
            "issues": [],
        }

        try:
            # Define expected cascade relationships
            expected_cascades = [
                {
                    "parent_table": "data_imports",
                    "child_table": "raw_import_records",
                    "foreign_key": "data_import_id",
                    "expected_action": "CASCADE",
                    "description": "Raw import records should be deleted when data import is deleted",
                },
                {
                    "parent_table": "client_accounts",
                    "child_table": "data_imports",
                    "foreign_key": "client_account_id",
                    "expected_action": "RESTRICT",
                    "description": "Data imports should prevent client account deletion",
                },
                {
                    "parent_table": "client_accounts",
                    "child_table": "discovery_flows",
                    "foreign_key": "client_account_id",
                    "expected_action": "CASCADE",
                    "description": "Discovery flows should be deleted when client account is deleted",
                },
                {
                    "parent_table": "client_accounts",
                    "child_table": "crewai_flow_state_extensions",
                    "foreign_key": "client_account_id",
                    "expected_action": "CASCADE",
                    "description": "CrewAI flow states should be deleted when client account is deleted",
                },
            ]

            for cascade in expected_cascades:
                await self._validate_single_cascade(session, cascade, results)

            if results["missing_cascades"]:
                results["valid"] = False
                logger.error(
                    f"❌ Found {len(results['missing_cascades'])} missing cascade configurations"
                )
            else:
                logger.info("✅ All cascade configurations are correct")

        except Exception as e:
            logger.error(f"❌ Cascade validation failed: {str(e)}", exc_info=True)
            results["valid"] = False
            results["issues"].append(f"Cascade validation error: {str(e)}")

        return results

    async def _validate_single_cascade(
        self, session: AsyncSession, cascade: Dict[str, str], results: Dict[str, Any]
    ):
        """Validate a single cascade configuration"""
        try:
            # Query PostgreSQL system tables to check foreign key constraints
            query = text(
                """
                SELECT
                    tc.constraint_name,
                    kcu.column_name as foreign_key_column,
                    ccu.table_name AS parent_table_name,
                    ccu.column_name AS parent_column_name,
                    rc.delete_rule,
                    rc.update_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                    AND tc.table_schema = rc.constraint_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = :child_table
                    AND kcu.column_name = :foreign_key
                    AND ccu.table_name = :parent_table
            """
            )

            result = await session.execute(
                query,
                {
                    "child_table": cascade["child_table"],
                    "foreign_key": cascade["foreign_key"],
                    "parent_table": cascade["parent_table"],
                },
            )

            constraint_info = result.fetchone()

            if constraint_info:
                cascade_rule = {
                    "parent_table": cascade["parent_table"],
                    "child_table": cascade["child_table"],
                    "foreign_key": cascade["foreign_key"],
                    "constraint_name": constraint_info.constraint_name,
                    "delete_rule": constraint_info.delete_rule,
                    "update_rule": constraint_info.update_rule,
                    "expected_action": cascade["expected_action"],
                    "description": cascade["description"],
                    "valid": constraint_info.delete_rule.upper()
                    == cascade["expected_action"].upper(),
                }

                results["cascade_rules"].append(cascade_rule)

                if not cascade_rule["valid"]:
                    results["missing_cascades"].append(cascade_rule)
                    results["issues"].append(
                        f"Incorrect cascade for {cascade['child_table']}.{cascade['foreign_key']}: "
                        f"expected {cascade['expected_action']}, got {constraint_info.delete_rule}"
                    )
                    logger.warning(
                        f"⚠️ Incorrect cascade rule: {cascade['child_table']}.{cascade['foreign_key']} "
                        f"(expected: {cascade['expected_action']}, actual: {constraint_info.delete_rule})"
                    )
                else:
                    logger.debug(
                        f"✅ Correct cascade rule: {cascade['child_table']}.{cascade['foreign_key']}"
                    )
            else:
                missing_cascade = {
                    "parent_table": cascade["parent_table"],
                    "child_table": cascade["child_table"],
                    "foreign_key": cascade["foreign_key"],
                    "expected_action": cascade["expected_action"],
                    "description": cascade["description"],
                    "constraint_name": None,
                    "delete_rule": None,
                    "valid": False,
                }

                results["missing_cascades"].append(missing_cascade)
                results["issues"].append(
                    f"Missing foreign key constraint: {cascade['child_table']}.{cascade['foreign_key']} -> "
                    f"{cascade['parent_table']}"
                )
                logger.error(
                    f"❌ Missing foreign key constraint: {cascade['child_table']}.{cascade['foreign_key']}"
                )

        except Exception as e:
            logger.error(
                f"❌ Failed to validate cascade for {cascade['child_table']}: {str(e)}"
            )
            results["issues"].append(
                f"Failed to validate cascade for {cascade['child_table']}: {str(e)}"
            )

    async def test_constraint_enforcement(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Test that database constraints are properly enforced.

        Returns:
            Dict containing constraint enforcement test results
        """
        logger.info("🧪 Testing constraint enforcement...")

        results = {
            "valid": True,
            "constraint_tests": [],
            "failed_tests": [],
            "issues": [],
        }

        try:
            # Define constraint tests to run
            constraint_tests = [
                {
                    "name": "foreign_key_enforcement",
                    "description": "Test that foreign key constraints prevent invalid insertions",
                    "test_type": "foreign_key",
                },
                {
                    "name": "not_null_enforcement",
                    "description": "Test that NOT NULL constraints are enforced",
                    "test_type": "not_null",
                },
                {
                    "name": "unique_constraint_enforcement",
                    "description": "Test that unique constraints prevent duplicates",
                    "test_type": "unique",
                },
            ]

            for test in constraint_tests:
                await self._run_constraint_test(session, test, results)

            if results["failed_tests"]:
                results["valid"] = False
                logger.error(
                    f"❌ {len(results['failed_tests'])} constraint tests failed"
                )
            else:
                logger.info("✅ All constraint enforcement tests passed")

        except Exception as e:
            logger.error(
                f"❌ Constraint enforcement testing failed: {str(e)}", exc_info=True
            )
            results["valid"] = False
            results["issues"].append(f"Constraint testing error: {str(e)}")

        return results

    async def _run_constraint_test(
        self, session: AsyncSession, test: Dict[str, str], results: Dict[str, Any]
    ):
        """Run a single constraint enforcement test"""
        test_result = {
            "test_name": test["name"],
            "description": test["description"],
            "test_type": test["test_type"],
            "passed": False,
            "error_message": None,
        }

        try:
            if test["test_type"] == "foreign_key":
                await self._test_foreign_key_constraint(session, test_result)
            elif test["test_type"] == "not_null":
                await self._test_not_null_constraint(session, test_result)
            elif test["test_type"] == "unique":
                await self._test_unique_constraint(session, test_result)

            results["constraint_tests"].append(test_result)

            if not test_result["passed"]:
                results["failed_tests"].append(test_result)
                results["issues"].append(
                    f"Constraint test failed: {test['name']} - {test_result.get('error_message', 'Unknown error')}"
                )
                logger.warning(f"⚠️ Constraint test failed: {test['name']}")
            else:
                logger.debug(f"✅ Constraint test passed: {test['name']}")

        except Exception as e:
            test_result["error_message"] = str(e)
            results["constraint_tests"].append(test_result)
            results["failed_tests"].append(test_result)
            logger.error(
                f"❌ Constraint test {test['name']} failed with exception: {str(e)}"
            )

    async def _test_foreign_key_constraint(
        self, session: AsyncSession, test_result: Dict[str, Any]
    ):
        """Test foreign key constraint enforcement"""
        try:
            # Attempt to insert a record with an invalid foreign key
            invalid_uuid = str(uuid.uuid4())

            # Try to insert a raw_import_record with non-existent data_import_id
            insert_query = text(
                """
                INSERT INTO raw_import_records (id, data_import_id, raw_data, created_at)
                VALUES (:id, :invalid_data_import_id, '{}', NOW())
            """
            )

            await session.execute(
                insert_query,
                {"id": str(uuid.uuid4()), "invalid_data_import_id": invalid_uuid},
            )

            # If we get here, the constraint didn't work
            test_result["passed"] = False
            test_result["error_message"] = (
                "Foreign key constraint did not prevent invalid insertion"
            )

            # Clean up the invalid record
            await session.rollback()

        except Exception as e:
            # An exception is expected - it means the constraint worked
            if (
                "foreign key constraint" in str(e).lower()
                or "violates" in str(e).lower()
            ):
                test_result["passed"] = True
                await session.rollback()  # Clean up the failed transaction
            else:
                test_result["passed"] = False
                test_result["error_message"] = f"Unexpected error: {str(e)}"
                await session.rollback()

    async def _test_not_null_constraint(
        self, session: AsyncSession, test_result: Dict[str, Any]
    ):
        """Test NOT NULL constraint enforcement"""
        try:
            # Attempt to insert a record with NULL in a NOT NULL field
            insert_query = text(
                """
                INSERT INTO client_accounts (id, name, created_at)
                VALUES (:id, NULL, NOW())
            """
            )

            await session.execute(insert_query, {"id": str(uuid.uuid4())})

            # If we get here, the constraint didn't work
            test_result["passed"] = False
            test_result["error_message"] = (
                "NOT NULL constraint did not prevent NULL insertion"
            )

            # Clean up
            await session.rollback()

        except Exception as e:
            # An exception is expected - it means the constraint worked
            if "not null" in str(e).lower() or "violates" in str(e).lower():
                test_result["passed"] = True
                await session.rollback()
            else:
                test_result["passed"] = False
                test_result["error_message"] = f"Unexpected error: {str(e)}"
                await session.rollback()

    async def _test_unique_constraint(
        self, session: AsyncSession, test_result: Dict[str, Any]
    ):
        """Test unique constraint enforcement"""
        try:
            # First, insert a test record
            test_id = str(uuid.uuid4())
            test_name = f"test_constraint_{test_id[:8]}"

            insert_query = text(
                """
                INSERT INTO client_accounts (id, name, created_at)
                VALUES (:id, :name, NOW())
            """
            )

            await session.execute(insert_query, {"id": test_id, "name": test_name})

            # Now try to insert a duplicate
            duplicate_query = text(
                """
                INSERT INTO client_accounts (id, name, created_at)
                VALUES (:id, :name, NOW())
            """
            )

            await session.execute(
                duplicate_query,
                {"id": str(uuid.uuid4()), "name": test_name},  # Duplicate name
            )

            # If we get here, the constraint didn't work
            test_result["passed"] = False
            test_result["error_message"] = (
                "Unique constraint did not prevent duplicate insertion"
            )

            # Clean up
            await session.rollback()

        except Exception as e:
            # An exception is expected - it means the constraint worked
            if (
                "unique" in str(e).lower()
                or "duplicate" in str(e).lower()
                or "violates" in str(e).lower()
            ):
                test_result["passed"] = True
                await session.rollback()
            else:
                test_result["passed"] = False
                test_result["error_message"] = f"Unexpected error: {str(e)}"
                await session.rollback()

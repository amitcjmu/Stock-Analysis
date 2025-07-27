#!/usr/bin/env python3
"""
Final Data Integrity Test - Phase 3 Validation
===============================================

Demonstrates that the data integrity fixes are working correctly by:
1. Testing foreign key relationships
2. Verifying data import to master flow linkage
3. Checking discovery flow to master flow linkage
4. Validating raw import record relationships

Usage:
    python scripts/test_data_integrity_final.py
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.core.database import AsyncSessionLocal


class DataIntegrityTester:
    """Tests data integrity after Phase 3 fixes."""

    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def test_result(self, test_name: str, passed: bool, message: str):
        """Record test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append(f"{status} {test_name}: {message}")

        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

    async def test_data_import_linkage(self, session):
        """Test that all data imports are linked to master flows."""
        # Check total data imports
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.data_imports")
        )
        total_count = total_result.scalar()

        # Check linked data imports
        linked_result = await session.execute(
            text(
                "SELECT COUNT(*) FROM migration.data_imports WHERE master_flow_id IS NOT NULL"
            )
        )
        linked_count = linked_result.scalar()

        # Check that all linked master flows exist
        valid_links_result = await session.execute(
            text(
                """
                SELECT COUNT(*) FROM migration.data_imports di
                JOIN migration.crewai_flow_state_extensions cfse ON di.master_flow_id = cfse.id
            """
            )
        )
        valid_links_count = valid_links_result.scalar()

        # Test 1: All data imports have master_flow_id
        self.test_result(
            "Data Import Master Flow Linkage",
            linked_count == total_count,
            f"{linked_count}/{total_count} data imports linked to master flows",
        )

        # Test 2: All links are valid (no orphaned references)
        self.test_result(
            "Data Import Valid References",
            valid_links_count == linked_count,
            f"{valid_links_count}/{linked_count} links are valid (no orphaned references)",
        )

    async def test_raw_import_record_linkage(self, session):
        """Test that all raw import records are properly linked."""
        # Check total raw import records
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.raw_import_records")
        )
        total_count = total_result.scalar()

        # Check records with master_flow_id
        master_linked_result = await session.execute(
            text(
                "SELECT COUNT(*) FROM migration.raw_import_records WHERE master_flow_id IS NOT NULL"
            )
        )
        master_linked_count = master_linked_result.scalar()

        # Check records with data_import_id
        data_linked_result = await session.execute(
            text(
                "SELECT COUNT(*) FROM migration.raw_import_records WHERE data_import_id IS NOT NULL"
            )
        )
        data_linked_count = data_linked_result.scalar()

        # Check valid data import links
        valid_data_links_result = await session.execute(
            text(
                """
                SELECT COUNT(*) FROM migration.raw_import_records rir
                JOIN migration.data_imports di ON rir.data_import_id = di.id
            """
            )
        )
        valid_data_links_count = valid_data_links_result.scalar()

        # Check valid master flow links
        valid_master_links_result = await session.execute(
            text(
                """
                SELECT COUNT(*) FROM migration.raw_import_records rir
                JOIN migration.crewai_flow_state_extensions cfse ON rir.master_flow_id = cfse.id
            """
            )
        )
        valid_master_links_count = valid_master_links_result.scalar()

        # Test 1: All raw records have master_flow_id
        self.test_result(
            "Raw Records Master Flow Linkage",
            master_linked_count == total_count,
            f"{master_linked_count}/{total_count} raw records linked to master flows",
        )

        # Test 2: All raw records have data_import_id
        self.test_result(
            "Raw Records Data Import Linkage",
            data_linked_count == total_count,
            f"{data_linked_count}/{total_count} raw records linked to data imports",
        )

        # Test 3: All data import links are valid
        self.test_result(
            "Raw Records Valid Data Import References",
            valid_data_links_count == data_linked_count,
            f"{valid_data_links_count}/{data_linked_count} data import links are valid",
        )

        # Test 4: All master flow links are valid
        self.test_result(
            "Raw Records Valid Master Flow References",
            valid_master_links_count == master_linked_count,
            f"{valid_master_links_count}/{master_linked_count} master flow links are valid",
        )

    async def test_discovery_flow_linkage(self, session):
        """Test discovery flow to master flow linkage."""
        # Check total discovery flows
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.discovery_flows")
        )
        total_count = total_result.scalar()

        # Check linked discovery flows
        linked_result = await session.execute(
            text(
                "SELECT COUNT(*) FROM migration.discovery_flows WHERE master_flow_id IS NOT NULL"
            )
        )
        linked_count = linked_result.scalar()

        # Check valid links
        valid_links_result = await session.execute(
            text(
                """
                SELECT COUNT(*) FROM migration.discovery_flows df
                JOIN migration.crewai_flow_state_extensions cfse ON df.master_flow_id = cfse.id
            """
            )
        )
        valid_links_count = valid_links_result.scalar()

        # Check flow_id matching (should match when both exist)
        flow_id_matches_result = await session.execute(
            text(
                """
                SELECT COUNT(*) FROM migration.discovery_flows df
                JOIN migration.crewai_flow_state_extensions cfse ON df.master_flow_id = cfse.id
                WHERE df.flow_id = cfse.flow_id
            """
            )
        )
        flow_id_matches_count = flow_id_matches_result.scalar()

        # Test 1: Discovery flow linkage
        linkage_percentage = (
            (linked_count / total_count * 100) if total_count > 0 else 0
        )
        self.test_result(
            "Discovery Flow Master Flow Linkage",
            linkage_percentage >= 90,  # Allow for some orphaned flows
            f"{linked_count}/{total_count} discovery flows linked ({linkage_percentage:.1f}%)",
        )

        # Test 2: Valid references
        self.test_result(
            "Discovery Flow Valid References",
            valid_links_count == linked_count,
            f"{valid_links_count}/{linked_count} links are valid",
        )

        # Test 3: Flow ID consistency
        self.test_result(
            "Discovery Flow ID Consistency",
            flow_id_matches_count == valid_links_count,
            f"{flow_id_matches_count}/{valid_links_count} flow_ids match between tables",
        )

    async def test_master_flow_utilization(self, session):
        """Test master flow utilization."""
        # Check total master flows
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.crewai_flow_state_extensions")
        )
        total_count = total_result.scalar()

        # Check master flows with children
        utilized_result = await session.execute(
            text(
                """
                SELECT COUNT(DISTINCT cfse.id) FROM migration.crewai_flow_state_extensions cfse
                WHERE EXISTS (
                    SELECT 1 FROM migration.data_imports di WHERE di.master_flow_id = cfse.id
                ) OR EXISTS (
                    SELECT 1 FROM migration.discovery_flows df WHERE df.master_flow_id = cfse.id
                )
            """
            )
        )
        utilized_count = utilized_result.scalar()

        # Check orphaned master flows
        orphaned_count = total_count - utilized_count
        utilization_percentage = (
            (utilized_count / total_count * 100) if total_count > 0 else 0
        )

        # Test master flow utilization
        self.test_result(
            "Master Flow Utilization",
            utilization_percentage >= 40,  # Reasonable utilization threshold
            f"{utilized_count}/{total_count} master flows have children ({utilization_percentage:.1f}%), {orphaned_count} orphaned",
        )

    async def test_data_consistency(self, session):
        """Test cross-table data consistency."""
        # Check tenant context consistency between data imports and master flows
        inconsistent_tenant_result = await session.execute(
            text(
                """
                SELECT COUNT(*) FROM migration.data_imports di
                JOIN migration.crewai_flow_state_extensions cfse ON di.master_flow_id = cfse.id
                WHERE di.client_account_id != cfse.client_account_id
                   OR di.engagement_id != cfse.engagement_id
            """
            )
        )
        inconsistent_tenant_count = inconsistent_tenant_result.scalar()

        # Check for data imports without raw records
        imports_without_records_result = await session.execute(
            text(
                """
                SELECT COUNT(*) FROM migration.data_imports di
                WHERE NOT EXISTS (
                    SELECT 1 FROM migration.raw_import_records rir
                    WHERE rir.data_import_id = di.id
                )
            """
            )
        )
        imports_without_records_count = imports_without_records_result.scalar()

        # Test 1: Tenant context consistency
        self.test_result(
            "Tenant Context Consistency",
            inconsistent_tenant_count == 0,
            f"{inconsistent_tenant_count} data imports have mismatched tenant context with their master flows",
        )

        # Test 2: Data imports have raw records
        self.test_result(
            "Data Import Completeness",
            imports_without_records_count <= 2,  # Allow for a few edge cases
            f"{imports_without_records_count} data imports have no raw records",
        )

    async def run_all_tests(self):
        """Run all data integrity tests."""
        print("🧪 Running Phase 3 Data Integrity Tests...")
        print("=" * 60)

        try:
            async with AsyncSessionLocal() as session:
                await self.test_data_import_linkage(session)
                await self.test_raw_import_record_linkage(session)
                await self.test_discovery_flow_linkage(session)
                await self.test_master_flow_utilization(session)
                await self.test_data_consistency(session)

        except Exception as e:
            self.test_result(
                "Database Connection", False, f"Failed to connect: {str(e)}"
            )

        # Print results
        print("\n📋 TEST RESULTS:")
        print("-" * 60)
        for result in self.test_results:
            print(result)

        print("\n📊 SUMMARY:")
        print("-" * 60)
        total_tests = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0

        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Success Rate: {success_rate:.1f}%")

        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED - Data integrity is excellent!")
        elif success_rate >= 90:
            print("\n✅ MOSTLY SUCCESSFUL - Minor issues remain")
        elif success_rate >= 70:
            print("\n⚠️  SOME ISSUES - Further work needed")
        else:
            print("\n❌ SIGNIFICANT ISSUES - Major problems detected")

        print("=" * 60)

        return self.tests_failed == 0


async def main():
    """Main entry point."""
    tester = DataIntegrityTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

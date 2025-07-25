#!/usr/bin/env python3
"""
Test script to verify the database migration works correctly.
This script performs a dry-run test of the migration logic.
"""

import asyncio
import sys

from sqlalchemy import text

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend")

from app.core.database import AsyncSessionLocal


async def test_migration():
    """Test the migration by checking foreign key constraints"""
    print("🧪 Testing migration foreign key constraints...")

    try:
        async with AsyncSessionLocal() as session:
            # Test 1: Check if foreign key constraints exist
            result = await session.execute(
                text(
                    """
                    SELECT
                        tc.table_name,
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name,
                        rc.delete_rule
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON tc.constraint_name = ccu.constraint_name
                    JOIN information_schema.referential_constraints rc
                        ON tc.constraint_name = rc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND kcu.column_name = 'master_flow_id'
                        AND tc.table_name IN ('discovery_flows', 'data_imports', 'raw_import_records')
                    ORDER BY tc.table_name
                """
                )
            )

            constraints = result.fetchall()

            print(f"Found {len(constraints)} foreign key constraints:")
            for constraint in constraints:
                print(
                    f"  📋 {constraint.table_name}.{constraint.column_name} -> {constraint.foreign_table_name}.{constraint.foreign_column_name}"
                )
                print(f"     Constraint: {constraint.constraint_name}")
                print(f"     Delete rule: {constraint.delete_rule}")
                print()

            # Test 2: Check if the constraints reference the correct column
            correct_constraints = []
            for constraint in constraints:
                if constraint.foreign_column_name == "flow_id":
                    correct_constraints.append(constraint)
                    print(f"✅ {constraint.table_name}: References flow_id correctly")
                else:
                    print(
                        f"❌ {constraint.table_name}: References {constraint.foreign_column_name} (should be flow_id)"
                    )

            print("\n📊 Summary:")
            print(f"   Total constraints: {len(constraints)}")
            print(f"   Correct constraints: {len(correct_constraints)}")
            print(
                f"   Migration needed: {'No' if len(correct_constraints) == len(constraints) else 'Yes'}"
            )

            # Test 3: Check if tables exist
            tables_to_check = [
                "crewai_flow_state_extensions",
                "discovery_flows",
                "data_imports",
                "raw_import_records",
            ]
            for table in tables_to_check:
                result = await session.execute(
                    text(
                        f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'"
                    )
                )
                count = result.scalar()
                print(f"   Table {table}: {'✅ EXISTS' if count > 0 else '❌ MISSING'}")

            return (
                len(correct_constraints) == len(constraints) and len(constraints) >= 3
            )

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🧪 Running migration test...\n")

    success = await test_migration()

    if success:
        print("\n✅ Migration test PASSED - All foreign key constraints are correct!")
        return 0
    else:
        print("\n❌ Migration test FAILED - Migration is needed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

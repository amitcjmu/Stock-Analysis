#!/usr/bin/env python3
"""
Thoroughly clean all demo data from the database.
This handles all foreign key constraints properly.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text


async def clean_all_demo_data():
    """Clean all demo data handling FK constraints in proper order"""
    print("\n🧹 Thoroughly cleaning all demo data...")

    async with AsyncSessionLocal() as session:
        # Execute cleanup in proper order to avoid FK constraints
        cleanup_queries = [
            # First clear references in dependent tables
            "UPDATE users SET default_engagement_id = NULL, default_client_id = NULL WHERE email LIKE '%demo%' OR email LIKE '%@demo.%'",
            # Delete associations and roles
            "DELETE FROM user_account_associations WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%demo%' OR email LIKE '%@demo.%')",
            "DELETE FROM user_roles WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%demo%' OR email LIKE '%@demo.%')",
            "DELETE FROM user_profiles WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%demo%' OR email LIKE '%@demo.%')",
            # Delete discovery flows and related data
            "DELETE FROM import_field_mappings WHERE data_import_id IN (SELECT id FROM data_imports WHERE engagement_id IN (SELECT id FROM engagements WHERE client_account_id IN (SELECT id FROM client_accounts WHERE name LIKE 'Demo%' OR id = '11111111-1111-1111-1111-111111111111')))",
            "DELETE FROM raw_import_records WHERE data_import_id IN (SELECT id FROM data_imports WHERE engagement_id IN (SELECT id FROM engagements WHERE client_account_id IN (SELECT id FROM client_accounts WHERE name LIKE 'Demo%' OR id = '11111111-1111-1111-1111-111111111111')))",
            "DELETE FROM data_imports WHERE engagement_id IN (SELECT id FROM engagements WHERE client_account_id IN (SELECT id FROM client_accounts WHERE name LIKE 'Demo%' OR id = '11111111-1111-1111-1111-111111111111'))",
            "DELETE FROM discovery_flows WHERE client_account_id IN (SELECT id FROM client_accounts WHERE name LIKE 'Demo%' OR id = '11111111-1111-1111-1111-111111111111')",
            # Delete assets and dependencies
            "DELETE FROM asset_dependencies WHERE asset_id IN (SELECT id FROM assets WHERE client_account_id IN (SELECT id FROM client_accounts WHERE name LIKE 'Demo%' OR id = '11111111-1111-1111-1111-111111111111'))",
            "DELETE FROM assets WHERE client_account_id IN (SELECT id FROM client_accounts WHERE name LIKE 'Demo%' OR id = '11111111-1111-1111-1111-111111111111')",
            # Delete migration waves
            "DELETE FROM migration_waves WHERE client_account_id IN (SELECT id FROM client_accounts WHERE name LIKE 'Demo%' OR id = '11111111-1111-1111-1111-111111111111')",
            # Delete users
            "DELETE FROM users WHERE email LIKE '%demo%' OR email LIKE '%@demo.%' OR email IN ('demo@democorp.com', 'analyst@democorp.com', 'viewer@democorp.com', 'client.admin@democorp.com')",
            # Delete engagements
            "DELETE FROM engagements WHERE client_account_id IN (SELECT id FROM client_accounts WHERE name LIKE 'Demo%' OR id = '11111111-1111-1111-1111-111111111111')",
            # Finally delete client accounts
            "DELETE FROM client_accounts WHERE name LIKE 'Demo%' OR id = '11111111-1111-1111-1111-111111111111'",
        ]

        for query in cleanup_queries:
            try:
                result = await session.execute(text(query))
                if result.rowcount > 0:
                    print(
                        f"   ✅ Cleaned {result.rowcount} records: {query.split(' ')[2]} {query.split(' ')[3]}"
                    )
            except Exception as e:
                print(f"   ⚠️ Query failed: {query[:50]}... - {e}")

        await session.commit()
        print("\n✅ All demo data cleaned successfully!")


async def verify_cleanup():
    """Verify all demo data is gone"""
    print("\n🔍 Verifying cleanup...")
    async with AsyncSessionLocal() as session:
        checks = [
            (
                "SELECT COUNT(*) FROM users WHERE email LIKE '%demo%' OR email LIKE '%@demo.%'",
                "Demo users",
            ),
            (
                "SELECT COUNT(*) FROM client_accounts WHERE name LIKE 'Demo%'",
                "Demo clients",
            ),
            (
                "SELECT COUNT(*) FROM engagements WHERE name LIKE 'Demo%'",
                "Demo engagements",
            ),
            (
                "SELECT COUNT(*) FROM discovery_flows WHERE flow_name LIKE 'Demo%'",
                "Demo flows",
            ),
            ("SELECT COUNT(*) FROM assets WHERE name LIKE 'Demo%'", "Demo assets"),
        ]

        all_clean = True
        for query, label in checks:
            result = await session.execute(text(query))
            count = result.scalar()
            if count > 0:
                print(f"   ❌ {label}: {count} remaining")
                all_clean = False
            else:
                print(f"   ✅ {label}: 0")

        return all_clean


async def main():
    """Main cleanup process"""
    print("=" * 60)
    print("🧹 DEMO DATA CLEANUP")
    print("=" * 60)

    try:
        await clean_all_demo_data()
        all_clean = await verify_cleanup()

        if all_clean:
            print("\n✅ All demo data successfully removed!")
        else:
            print("\n⚠️ Some demo data remains - manual cleanup may be needed")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

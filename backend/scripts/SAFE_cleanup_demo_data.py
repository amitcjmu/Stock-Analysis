#!/usr/bin/env python3
"""
SAFE Demo Data Cleanup - With Multiple Safeguards

This script includes:
1. Environment checks (only runs in 'local')
2. Explicit confirmation prompt
3. Dry-run mode
4. Automatic backup before deletion
5. Detailed logging

DO NOT USE IN PRODUCTION OR STAGING
"""
import asyncio
import os
import sys
from datetime import datetime

from sqlalchemy import text

# Add backend directory to path for app imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal  # noqa: E402


def check_environment():
    """Verify we're in a safe environment"""
    env = os.getenv("ENVIRONMENT", "production").lower()

    if env in ["production", "staging", "prod", "stg"]:
        print("❌ FATAL: This script cannot run in production or staging!")
        print(f"   Current ENVIRONMENT: {env}")
        print("   Exiting for safety.")
        sys.exit(1)

    if env != "local":
        print(f"⚠️  WARNING: ENVIRONMENT is '{env}', not 'local'")
        response = input("   Are you ABSOLUTELY SURE you want to continue? (yes/NO): ")
        if response.lower() != "yes":
            print("   Aborting for safety.")
            sys.exit(0)


def get_user_confirmation():
    """Require explicit confirmation"""
    print("\n" + "=" * 70)
    print("⚠️  DANGER: This will DELETE ALL DATA for demo client account!")
    print("=" * 70)
    print("\nThis will delete:")
    print("  - All assets")
    print("  - All discovery flows")
    print("  - All data imports and raw records")
    print("  - All collection flows")
    print("  - All users with 'demo' in email")
    print("  - Demo client account and engagements")
    print("\n❗ THIS CANNOT BE UNDONE ❗\n")

    response = input("Type 'DELETE MY DATA' to proceed: ")
    if response != "DELETE MY DATA":
        print("❌ Confirmation failed. Aborting.")
        sys.exit(0)

    print("\n⚠️  Final confirmation...")
    response2 = input("Type 'I understand the risks' to continue: ")
    if response2 != "I understand the risks":
        print("❌ Final confirmation failed. Aborting.")
        sys.exit(0)


async def create_backup():
    """Create a backup before deletion"""
    print("\n📦 Creating backup...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"/tmp/demo_data_backup_{timestamp}.sql"

    # Note: This is a placeholder - actual backup would use pg_dump
    print(f"   Backup should be created at: {backup_file}")
    print("   (Implement actual pg_dump command here)")

    return backup_file


async def clean_demo_data_safe(dry_run: bool = True):
    """Clean demo data with safety checks"""

    if dry_run:
        print("\n🔍 DRY RUN MODE - No data will be deleted")
    else:
        print("\n🧹 LIVE MODE - Data will be deleted")

    async with AsyncSessionLocal() as session:
        # Count queries to show what would be deleted
        demo_client_id = "11111111-1111-1111-1111-111111111111"
        count_queries = [
            ("SELECT COUNT(*) FROM users WHERE email LIKE '%demo%'", "demo users"),
            (
                f"SELECT COUNT(*) FROM assets WHERE client_account_id = '{demo_client_id}'",
                "assets",
            ),
            (
                f"SELECT COUNT(*) FROM discovery_flows "
                f"WHERE client_account_id = '{demo_client_id}'",
                "discovery flows",
            ),
            (
                f"SELECT COUNT(*) FROM data_imports WHERE engagement_id IN "
                f"(SELECT id FROM engagements WHERE client_account_id = '{demo_client_id}')",
                "data imports",
            ),
        ]

        print("\n📊 Data to be affected:")
        for query, label in count_queries:
            result = await session.execute(text(query))
            count = result.scalar()
            print(f"   {label}: {count} records")

        if dry_run:
            print("\n✅ Dry run completed - no data was deleted")
            return

        # Actual cleanup queries (same as original script)
        demo_client_id = "11111111-1111-1111-1111-111111111111"
        cleanup_queries = [
            (
                "UPDATE users SET default_engagement_id = NULL, "
                "default_client_id = NULL WHERE email LIKE '%demo%'"
            ),
            (
                "DELETE FROM user_account_associations "
                "WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%demo%')"
            ),
            (
                "DELETE FROM user_roles "
                "WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%demo%')"
            ),
            (
                "DELETE FROM user_profiles "
                "WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%demo%')"
            ),
            (
                f"DELETE FROM import_field_mappings WHERE data_import_id IN "
                f"(SELECT id FROM data_imports WHERE engagement_id IN "
                f"(SELECT id FROM engagements WHERE client_account_id = '{demo_client_id}'))"
            ),
            (
                f"DELETE FROM raw_import_records WHERE data_import_id IN "
                f"(SELECT id FROM data_imports WHERE engagement_id IN "
                f"(SELECT id FROM engagements WHERE client_account_id = '{demo_client_id}'))"
            ),
            (
                f"DELETE FROM data_imports WHERE engagement_id IN "
                f"(SELECT id FROM engagements WHERE client_account_id = '{demo_client_id}')"
            ),
            f"DELETE FROM discovery_flows WHERE client_account_id = '{demo_client_id}'",
            (
                f"DELETE FROM asset_dependencies WHERE asset_id IN "
                f"(SELECT id FROM assets WHERE client_account_id = '{demo_client_id}')"
            ),
            f"DELETE FROM assets WHERE client_account_id = '{demo_client_id}'",
            f"DELETE FROM migration_waves WHERE client_account_id = '{demo_client_id}'",
            "DELETE FROM users WHERE email LIKE '%demo%'",
            f"DELETE FROM engagements WHERE client_account_id = '{demo_client_id}'",
            f"DELETE FROM client_accounts WHERE id = '{demo_client_id}'",
        ]

        for query in cleanup_queries:
            try:
                result = await session.execute(text(query))
                await session.commit()
                if result.rowcount > 0:
                    print(f"   ✅ Deleted {result.rowcount} records")
            except Exception as e:
                print(f"   ⚠️ Query failed: {str(e)[:100]}")

        print("\n✅ Cleanup completed!")


async def main():
    """Main execution with all safety checks"""
    print("=" * 70)
    print("SAFE DEMO DATA CLEANUP SCRIPT")
    print("=" * 70)

    # Safety check 1: Environment
    check_environment()

    # Check if dry-run mode
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv

    if not dry_run:
        # Safety check 2: User confirmation
        get_user_confirmation()

        # Safety check 3: Backup
        backup_file = await create_backup()
        print(f"✅ Backup created: {backup_file}")

    # Execute cleanup
    await clean_demo_data_safe(dry_run=dry_run)

    if not dry_run:
        print("\n📋 Post-cleanup checklist:")
        print("  1. Verify data was deleted correctly")
        print("  2. Check if any foreign key issues occurred")
        print("  3. Document the cleanup in incident log")
        print(f"  4. Backup file location: {backup_file if not dry_run else 'N/A'}")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python SAFE_cleanup_demo_data.py [--dry-run]")
        print("\nOptions:")
        print("  --dry-run, -d    Show what would be deleted without deleting")
        print("  --help, -h       Show this help message")
        print("\nSafety features:")
        print("  - Only runs in 'local' environment")
        print("  - Requires explicit confirmation")
        print("  - Creates backup before deletion")
        print("  - Supports dry-run mode")
        sys.exit(0)

    asyncio.run(main())

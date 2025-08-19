#!/usr/bin/env python3
"""
Cleanup Test Data Field Mappings

This script removes field mappings that contain test data patterns
(like Device_ID, Device_Name, etc.) that should not exist in production.

Usage:
    python scripts/cleanup_test_data_mappings.py [--dry-run] [--client-id CLIENT_ID]

Options:
    --dry-run       Show what would be deleted without actually deleting
    --client-id     Target specific client account ID (optional)
"""

import asyncio
import logging
import argparse
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.data_import.mapping import ImportFieldMapping

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test data patterns to identify and remove
TEST_DATA_PATTERNS = [
    "Device_ID",
    "Device_Name",
    "Device_Type",
    "IP_Address",
    "Status_Code",
    "Location",
]

# Additional patterns that indicate test data
TEST_DATA_PREFIXES = ["Device_", "Test_", "DEMO_"]


def is_test_data_field(source_field: str) -> bool:
    """Check if a source field contains test data patterns."""
    if not source_field:
        return False

    # Check exact matches
    if source_field in TEST_DATA_PATTERNS:
        return True

    # Check prefixes
    for prefix in TEST_DATA_PREFIXES:
        if source_field.startswith(prefix):
            return True

    return False


async def find_test_data_mappings(
    session: AsyncSession, client_account_id: Optional[str] = None
) -> List[ImportFieldMapping]:
    """Find all field mappings that contain test data patterns."""

    query = select(ImportFieldMapping)

    if client_account_id:
        query = query.where(ImportFieldMapping.client_account_id == client_account_id)

    result = await session.execute(query)
    all_mappings = result.scalars().all()

    # Filter for test data patterns
    test_mappings = []
    for mapping in all_mappings:
        if is_test_data_field(mapping.source_field):
            test_mappings.append(mapping)

    return test_mappings


async def cleanup_test_data_mappings(
    dry_run: bool = True, client_account_id: Optional[str] = None
) -> None:
    """Remove test data field mappings from the database."""

    logger.info("🧹 Starting test data cleanup process...")
    logger.info(f"   Mode: {'DRY RUN' if dry_run else 'LIVE DELETION'}")
    if client_account_id:
        logger.info(f"   Target client: {client_account_id}")
    else:
        logger.info("   Target: ALL clients")

    async with AsyncSessionLocal() as session:
        # Find test data mappings
        test_mappings = await find_test_data_mappings(session, client_account_id)

        if not test_mappings:
            logger.info("✅ No test data field mappings found!")
            return

        logger.warning(f"❌ Found {len(test_mappings)} test data field mappings:")

        # Group by import and source field for better reporting
        by_import = {}
        for mapping in test_mappings:
            import_id = str(mapping.data_import_id)
            if import_id not in by_import:
                by_import[import_id] = []
            by_import[import_id].append(mapping)

        # Report findings
        for import_id, mappings in by_import.items():
            logger.warning(f"   Import {import_id}:")
            for mapping in mappings:
                logger.warning(
                    f"     - {mapping.source_field} -> {mapping.target_field} "
                    f"(ID: {mapping.id}, Status: {mapping.status})"
                )

        if dry_run:
            logger.info("🔍 DRY RUN: Would delete these mappings")
            return

        # Confirm deletion
        print(f"\n⚠️  DANGER: About to delete {len(test_mappings)} field mappings!")
        print("   This action cannot be undone.")
        response = input("   Type 'DELETE' to confirm: ")

        if response != "DELETE":
            logger.info("❌ Deletion cancelled by user")
            return

        # Perform deletion
        logger.info(f"🗑️  Deleting {len(test_mappings)} test data field mappings...")

        deleted_count = 0
        for mapping in test_mappings:
            try:
                await session.delete(mapping)
                deleted_count += 1
                logger.info(f"   ✅ Deleted: {mapping.source_field} (ID: {mapping.id})")
            except Exception as e:
                logger.error(f"   ❌ Failed to delete {mapping.id}: {e}")

        # Commit the transaction
        await session.commit()

        logger.info(
            f"✅ Successfully deleted {deleted_count} test data field mappings!"
        )

        # Verify cleanup
        remaining_test_mappings = await find_test_data_mappings(
            session, client_account_id
        )
        if remaining_test_mappings:
            logger.warning(
                f"⚠️  {len(remaining_test_mappings)} test mappings still remain"
            )
        else:
            logger.info("🎉 All test data field mappings have been removed!")


async def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Cleanup test data field mappings from the database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--client-id", type=str, help="Target specific client account ID (optional)"
    )

    args = parser.parse_args()

    try:
        await cleanup_test_data_mappings(
            dry_run=args.dry_run, client_account_id=args.client_id
        )
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

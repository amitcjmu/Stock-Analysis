#!/usr/bin/env python3
"""
Script to delete all asset_dependencies records for clean testing.

Usage:
    docker-compose exec backend python scripts/delete_asset_dependencies.py
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import delete, func, select

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.database import get_db  # noqa: E402
from app.models.asset.relationships import AssetDependency  # noqa: E402


async def delete_all_dependencies():
    """Delete all asset_dependencies records."""
    async for db in get_db():
        try:
            # Count before deletion
            count_before = await db.execute(
                select(func.count()).select_from(AssetDependency)
            )
            before_count = count_before.scalar() or 0

            print(f"📊 Found {before_count} asset dependency records")

            if before_count == 0:
                print("✅ No dependencies to delete. Table is already clean.")
                return

            # Delete all dependencies
            result = await db.execute(delete(AssetDependency))
            await db.commit()

            # Count after deletion
            count_after = await db.execute(
                select(func.count()).select_from(AssetDependency)
            )
            after_count = count_after.scalar() or 0

            print(f"✅ Deleted {result.rowcount} asset dependency records")
            print(f"📊 Remaining records: {after_count}")

            if after_count == 0:
                print("✅ Asset dependencies table is now clean for testing!")
            else:
                print(f"⚠️  Warning: {after_count} records still exist after deletion")

        except Exception as e:
            await db.rollback()
            print(f"❌ Error deleting dependencies: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(delete_all_dependencies())

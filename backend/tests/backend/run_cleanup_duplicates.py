"""
Run the cleanup script for the specific client/engagement with duplicates
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.core.database import AsyncSessionLocal

from tests.backend.cleanup_duplicate_assets import (
    analyze_duplicates_by_flow,
    cleanup_duplicate_assets,
)


async def main():
    # Actual IDs from the database scan
    CLIENT_ACCOUNT_ID = "21990f3a-abb6-4862-be06-cb6f854e167b"
    ENGAGEMENT_ID = "58467010-6a72-44e8-ba37-cc0238724455"

    # Set to False to actually delete duplicates
    DRY_RUN = False  # ⚠️ This will DELETE data

    async with AsyncSessionLocal() as db:
        print(f"🧹 Running cleanup for client {CLIENT_ACCOUNT_ID}")
        print(f"   Engagement: {ENGAGEMENT_ID}")
        print(f"   Dry run: {DRY_RUN}")
        print("")

        # First analyze by flow
        flow_analysis = await analyze_duplicates_by_flow(
            db, CLIENT_ACCOUNT_ID, ENGAGEMENT_ID
        )
        for flow_id, stats in flow_analysis.items():
            print(f"Flow {flow_id}: {stats['duplicate_assets']} duplicates")

        # Run cleanup
        stats = await cleanup_duplicate_assets(
            db, CLIENT_ACCOUNT_ID, ENGAGEMENT_ID, dry_run=DRY_RUN
        )

        print("\n✅ Cleanup complete!")
        print(f"   Removed {stats.get('assets_deleted', 0)} duplicate assets")


if __name__ == "__main__":
    # Set the DATABASE_URL
    os.environ[
        "DATABASE_URL"
    ] = "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"
    asyncio.run(main())

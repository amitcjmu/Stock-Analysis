"""
Cleanup script to remove duplicate assets from the database.
This script identifies and removes duplicate assets based on hostname/name fields
while keeping the most recently created asset for each unique identifier.
"""

import asyncio
import logging
from typing import Dict, List

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def find_duplicate_assets(
    db: AsyncSession, client_account_id: str, engagement_id: str
) -> Dict[str, List[Asset]]:
    """Find duplicate assets grouped by their identifying fields"""

    # Get all assets for the client/engagement
    query = (
        select(Asset)
        .where(
            and_(
                Asset.client_account_id == client_account_id,
                Asset.engagement_id == engagement_id,
            )
        )
        .order_by(Asset.created_at.desc())
    )  # Order by newest first

    result = await db.execute(query)
    all_assets = result.scalars().all()

    logger.info(f"Found {len(all_assets)} total assets")

    # Group assets by their identifying fields
    asset_groups = {}

    for asset in all_assets:
        # Create a key based on identifying fields
        # Prioritize hostname, then name, then ip_address
        key = None

        if asset.hostname:
            key = f"hostname:{asset.hostname.lower()}"
        elif asset.name:
            key = f"name:{asset.name.lower()}"
        elif asset.ip_address:
            key = f"ip:{asset.ip_address}"
        else:
            # Skip assets without any identifying field
            continue

        if key not in asset_groups:
            asset_groups[key] = []
        asset_groups[key].append(asset)

    # Filter to only include groups with duplicates
    duplicate_groups = {
        key: assets for key, assets in asset_groups.items() if len(assets) > 1
    }

    logger.info(f"Found {len(duplicate_groups)} groups with duplicates")

    return duplicate_groups


async def cleanup_duplicate_assets(
    db: AsyncSession, client_account_id: str, engagement_id: str, dry_run: bool = True
) -> Dict[str, int]:
    """Remove duplicate assets, keeping the most recent one"""

    duplicate_groups = await find_duplicate_assets(db, client_account_id, engagement_id)

    stats = {"total_duplicates": 0, "assets_to_remove": 0, "groups_processed": 0}

    assets_to_delete = []

    for key, assets in duplicate_groups.items():
        stats["groups_processed"] += 1
        stats["total_duplicates"] += len(assets) - 1

        # Keep the first asset (newest) and mark others for deletion
        assets_to_keep = assets[0]
        assets_to_remove = assets[1:]

        logger.info(f"\nGroup: {key}")
        logger.info(
            f"  Keeping: {assets_to_keep.name} (created: {assets_to_keep.created_at})"
        )

        for asset in assets_to_remove:
            logger.info(f"  Removing: {asset.name} (created: {asset.created_at})")
            assets_to_delete.append(asset.id)
            stats["assets_to_remove"] += 1

    if dry_run:
        logger.info("\n🔍 DRY RUN - No assets were deleted")
        logger.info(f"Would delete {stats['assets_to_remove']} duplicate assets")
    else:
        # Delete the duplicate assets
        if assets_to_delete:
            delete_stmt = delete(Asset).where(Asset.id.in_(assets_to_delete))

            result = await db.execute(delete_stmt)
            await db.commit()

            logger.info(f"\n✅ Deleted {result.rowcount} duplicate assets")
            stats["assets_deleted"] = result.rowcount

    return stats


async def analyze_duplicates_by_flow(
    db: AsyncSession, client_account_id: str, engagement_id: str
) -> Dict[str, any]:
    """Analyze duplicates by discovery flow to understand the pattern"""

    duplicate_groups = await find_duplicate_assets(db, client_account_id, engagement_id)

    flow_analysis = {}

    for key, assets in duplicate_groups.items():
        for asset in assets:
            flow_id = (
                str(asset.discovery_flow_id) if asset.discovery_flow_id else "unknown"
            )

            if flow_id not in flow_analysis:
                flow_analysis[flow_id] = {
                    "total_assets": 0,
                    "duplicate_assets": 0,
                    "unique_keys": set(),
                }

            flow_analysis[flow_id]["total_assets"] += 1
            if len(assets) > 1:  # This is a duplicate
                flow_analysis[flow_id]["duplicate_assets"] += 1
                flow_analysis[flow_id]["unique_keys"].add(key)

    # Convert sets to lists for JSON serialization
    for flow_id in flow_analysis:
        flow_analysis[flow_id]["unique_keys"] = list(
            flow_analysis[flow_id]["unique_keys"]
        )

    return flow_analysis


async def main():
    """Main function to run the cleanup"""

    # Configuration - Update these values for your environment
    CLIENT_ACCOUNT_ID = "your-client-account-id"  # Replace with actual UUID
    ENGAGEMENT_ID = "your-engagement-id"  # Replace with actual UUID
    DRY_RUN = True  # Set to False to actually delete duplicates

    logger.info("🧹 Starting asset duplicate cleanup")
    logger.info(f"Client Account ID: {CLIENT_ACCOUNT_ID}")
    logger.info(f"Engagement ID: {ENGAGEMENT_ID}")
    logger.info(f"Dry Run: {DRY_RUN}")

    async with AsyncSessionLocal() as db:
        try:
            # First, analyze duplicates by flow
            logger.info("\n📊 Analyzing duplicates by discovery flow...")
            flow_analysis = await analyze_duplicates_by_flow(
                db, CLIENT_ACCOUNT_ID, ENGAGEMENT_ID
            )

            for flow_id, stats in flow_analysis.items():
                logger.info(f"\nFlow {flow_id}:")
                logger.info(f"  Total assets: {stats['total_assets']}")
                logger.info(f"  Duplicate assets: {stats['duplicate_assets']}")
                logger.info(f"  Unique duplicate groups: {len(stats['unique_keys'])}")

            # Then run the cleanup
            logger.info("\n🔧 Running duplicate cleanup...")
            stats = await cleanup_duplicate_assets(
                db, CLIENT_ACCOUNT_ID, ENGAGEMENT_ID, dry_run=DRY_RUN
            )

            logger.info("\n📈 Cleanup Summary:")
            logger.info(f"  Groups processed: {stats['groups_processed']}")
            logger.info(f"  Total duplicates found: {stats['total_duplicates']}")
            logger.info(f"  Assets to remove: {stats['assets_to_remove']}")

            if not DRY_RUN and "assets_deleted" in stats:
                logger.info(f"  Assets actually deleted: {stats['assets_deleted']}")

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    # Note: To run this script, you need to:
    # 1. Update CLIENT_ACCOUNT_ID and ENGAGEMENT_ID with actual values
    # 2. Set DRY_RUN to False when ready to delete
    # 3. Run from the backend directory: python -m tests.backend.cleanup_duplicate_assets

    asyncio.run(main())

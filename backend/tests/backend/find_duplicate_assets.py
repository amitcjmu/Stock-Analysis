"""
Quick script to find duplicate assets and get the client/engagement IDs
"""

import asyncio
import logging
from collections import defaultdict

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from sqlalchemy import and_, func, select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def find_all_duplicates():
    """Find all duplicate assets across all clients/engagements"""

    async with AsyncSessionLocal() as db:
        try:
            # First, get all unique client/engagement combinations
            query = select(
                Asset.client_account_id,
                Asset.engagement_id,
                func.count(Asset.id).label("total_assets"),
            ).group_by(Asset.client_account_id, Asset.engagement_id)

            result = await db.execute(query)
            client_engagements = result.all()

            logger.info(
                f"\n📊 Found {len(client_engagements)} client/engagement combinations"
            )

            for client_id, engagement_id, total_assets in client_engagements:
                logger.info(
                    f"\n🔍 Checking Client: {client_id}, Engagement: {engagement_id}"
                )
                logger.info(f"   Total assets: {total_assets}")

                # Get all assets for this client/engagement
                asset_query = (
                    select(Asset)
                    .where(
                        and_(
                            Asset.client_account_id == client_id,
                            Asset.engagement_id == engagement_id,
                        )
                    )
                    .order_by(Asset.created_at.desc())
                )

                result = await db.execute(asset_query)
                assets = result.scalars().all()

                # Find duplicates by hostname
                hostname_groups = defaultdict(list)
                name_groups = defaultdict(list)

                for asset in assets:
                    if asset.hostname:
                        hostname_groups[asset.hostname.lower()].append(asset)
                    elif asset.name:
                        name_groups[asset.name.lower()].append(asset)

                # Report duplicates
                duplicate_count = 0

                for hostname, group in hostname_groups.items():
                    if len(group) > 1:
                        duplicate_count += len(group) - 1
                        logger.info(
                            f"   Duplicate hostname '{hostname}': {len(group)} instances"
                        )
                        for asset in group[:3]:  # Show first 3
                            logger.info(
                                f"     - {asset.name} (created: {asset.created_at})"
                            )

                for name, group in name_groups.items():
                    if len(group) > 1:
                        duplicate_count += len(group) - 1
                        logger.info(
                            f"   Duplicate name '{name}': {len(group)} instances"
                        )
                        for asset in group[:3]:  # Show first 3
                            logger.info(f"     - Created: {asset.created_at}")

                if duplicate_count > 0:
                    logger.info(f"   ⚠️  Total duplicates: {duplicate_count}")
                    logger.info("   To clean up, run cleanup_duplicate_assets.py with:")
                    logger.info(f"     CLIENT_ACCOUNT_ID = '{client_id}'")
                    logger.info(f"     ENGAGEMENT_ID = '{engagement_id}'")
                else:
                    logger.info("   ✅ No duplicates found")

        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)


if __name__ == "__main__":
    # Run from backend directory: python -m tests.backend.find_duplicate_assets
    asyncio.run(find_all_duplicates())

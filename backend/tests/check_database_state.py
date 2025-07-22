#!/usr/bin/env python3
"""
Check Database State Script
"""

import asyncio
import sys

sys.path.append('/app')

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset


async def check_database_state():
    """Check the current state of assets and workflow in the database."""
    print("🔍 Checking Database State...")
    
    async with AsyncSessionLocal() as session:
        # Check assets
        asset_count = await session.execute(select(func.count(Asset.id)))
        asset_total = asset_count.scalar()
        print(f"📊 Total assets: {asset_total}")
        
        if asset_total > 0:
            # Get sample assets
            assets_result = await session.execute(select(Asset).limit(5))
            assets = assets_result.scalars().all()
            print("🎯 Sample assets:")
            for asset in assets:
                print(f"  - {asset.name} (ID: {asset.id}, Type: {asset.asset_type})")
                print(f"    Discovery status: {getattr(asset, 'discovery_status', 'N/A')}")
                print(f"    Mapping status: {getattr(asset, 'mapping_status', 'N/A')}")
                print(f"    Assessment readiness: {getattr(asset, 'assessment_readiness', 'N/A')}")
        else:
            print("❌ No assets found in database")
        
        # Check raw import records
        try:
            from app.models.data_import import RawImportRecord
            raw_count = await session.execute(select(func.count(RawImportRecord.id)))
            raw_total = raw_count.scalar()
            print(f"📋 Total raw import records: {raw_total}")
        except Exception as e:
            print(f"⚠️ Could not check raw import records: {e}")

if __name__ == "__main__":
    asyncio.run(check_database_state()) 
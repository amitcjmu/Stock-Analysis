#!/usr/bin/env python3
"""
Fix Asset Creation Script

This script:
1. Deletes existing assets with generic names
2. Triggers fresh asset creation with field mappings
3. Verifies the results
"""

import asyncio
import sys
import os
from typing import List

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db')

from app.core.database import get_db
from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from sqlalchemy import select, delete, and_


async def fix_asset_creation():
    """Fix asset creation by deleting generic assets and triggering fresh creation"""
    
    async for db in get_db():
        try:
            print("🔧 Asset Creation Fix Script")
            print("=" * 50)
            
            # Step 1: Find assets with generic names
            print("\n📋 Step 1: Finding assets with generic names...")
            
            generic_assets_query = select(Asset).where(
                Asset.name.like('unnamed_asset_%')
            )
            result = await db.execute(generic_assets_query)
            generic_assets = result.scalars().all()
            
            print(f"Found {len(generic_assets)} assets with generic names:")
            for asset in generic_assets:
                print(f"  - {asset.name} (ID: {asset.id})")
                print(f"    Hostname: {asset.hostname}")
                print(f"    IP: {asset.ip_address}")
                print(f"    Type: {asset.asset_type}")
            
            if not generic_assets:
                print("✅ No generic assets found - nothing to fix!")
                return
            
            # Step 2: Delete generic assets
            print(f"\n🗑️ Step 2: Deleting {len(generic_assets)} generic assets...")
            
            delete_query = delete(Asset).where(
                Asset.name.like('unnamed_asset_%')
            )
            await db.execute(delete_query)
            await db.commit()
            
            print("✅ Generic assets deleted successfully!")
            
            # Step 3: Find the discovery flow to trigger asset creation
            print(f"\n🔄 Step 3: Finding discovery flow to trigger asset creation...")
            
            flow_query = select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == 'e656e196-c5b0-4d78-8475-85330ec67657'
            )
            flow_result = await db.execute(flow_query)
            discovery_flow = flow_result.scalar_one_or_none()
            
            if not discovery_flow:
                print("❌ Discovery flow not found!")
                return
            
            print(f"✅ Found discovery flow: {discovery_flow.flow_name}")
            print(f"   Data import ID: {discovery_flow.data_import_id}")
            print(f"   Current phase: {discovery_flow.current_phase}")
            
            # Step 4: Reset flow state to trigger asset creation
            print(f"\n🔄 Step 4: Resetting flow state to trigger asset creation...")
            
            discovery_flow.asset_inventory_completed = False
            discovery_flow.current_phase = "asset_inventory"
            await db.commit()
            
            print("✅ Flow state reset - asset inventory phase will be triggered")
            
            # Step 5: Verify no assets exist
            print(f"\n✅ Step 5: Verifying assets are deleted...")
            
            remaining_query = select(Asset)
            remaining_result = await db.execute(remaining_query)
            remaining_assets = remaining_result.scalars().all()
            
            print(f"Remaining assets: {len(remaining_assets)}")
            if remaining_assets:
                print("Remaining assets:")
                for asset in remaining_assets:
                    print(f"  - {asset.name} (Type: {asset.asset_type})")
            
            print(f"\n🎯 Next Steps:")
            print(f"1. Call the assets API to trigger asset creation:")
            print(f"   curl -X GET 'http://localhost:8081/api/v1/unified-discovery/assets?page_size=100&flow_id=e656e196-c5b0-4d78-8475-85330ec67657' \\")
            print(f"     -H 'Authorization: Bearer YOUR_TOKEN' \\")
            print(f"     -H 'X-Client-Account-ID: 11111111-1111-1111-1111-111111111111' \\")
            print(f"     -H 'X-Engagement-ID: 22222222-2222-2222-2222-222222222222' \\")
            print(f"     -H 'X-User-ID: 33333333-3333-3333-3333-333333333333'")
            print(f"")
            print(f"2. Watch the backend logs for debug messages:")
            print(f"   docker logs migration_backend --tail 50 | grep -E '(📋|🔨|🔍|✅|❌|⚠️)'")
            print(f"")
            print(f"3. Verify assets are created with correct field mappings")
            
        except Exception as e:
            print(f"❌ Error during fix: {e}")
            import traceback
            traceback.print_exc()
        
        break


async def main():
    await fix_asset_creation()


if __name__ == "__main__":
    asyncio.run(main())



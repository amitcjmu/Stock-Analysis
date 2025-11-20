#!/usr/bin/env python3
"""
Test script to execute asset inventory on existing raw data
CC: Tests the asset creation pipeline with real data
"""

import asyncio
import sys

# Add the backend path so we can import modules
sys.path.insert(0, 'backend')

from app.core.database import AsyncSessionLocal
from app.services.flow_configs.discovery_handlers import asset_inventory
from sqlalchemy import text


async def test_existing_raw_data():
    """Test the asset inventory handler with existing raw data"""
    print("🧪 Testing Asset Inventory Handler with Existing Data")

    # Use the existing flow with raw data
    existing_flow_id = "bbda1263-99c6-4cd6-b44d-a084a5d919c8"
    client_id = "11111111-1111-1111-1111-111111111111"
    engagement_id = "22222222-2222-2222-2222-222222222222"

    async with AsyncSessionLocal() as db:
        try:
            # Check raw data count before
            result = await db.execute(
                text("SELECT COUNT(*) FROM migration.raw_import_records WHERE master_flow_id = :flow_id"),
                {"flow_id": existing_flow_id}
            )
            raw_count = result.scalar()
            print(f"📊 Found {raw_count} raw import records for flow {existing_flow_id}")

            # Check asset count before
            result = await db.execute(
                text("SELECT COUNT(*) FROM migration.assets WHERE master_flow_id = :flow_id"),
                {"flow_id": existing_flow_id}
            )
            assets_before = result.scalar()
            print(f"🎯 Assets before: {assets_before}")

            if raw_count == 0:
                print("❌ No raw data found to process")
                return

            # Create mock context
            class MockContext:
                def __init__(self, client_id, engagement_id, db_session):
                    self.client_account_id = client_id
                    self.engagement_id = engagement_id
                    self.user_id = "test-user"
                    self.db_session = db_session

            context = MockContext(client_id, engagement_id, db)

            # Prepare phase input
            phase_input = {
                "master_flow_id": existing_flow_id,
                "client_account_id": client_id,
                "engagement_id": engagement_id,
            }

            # Execute the asset inventory handler
            print(f"🔄 Executing asset inventory for flow: {existing_flow_id}")
            result = await asset_inventory(
                flow_id=existing_flow_id,
                phase_input=phase_input,
                context=context,
                db_session=db
            )

            print(f"📊 Handler result: {result}")

            # Check asset count after
            assets_result = await db.execute(
                "SELECT COUNT(*) FROM migration.assets WHERE master_flow_id = %s",
                (existing_flow_id,)
            )
            assets_after = assets_result.scalar()
            print(f"🎯 Assets after: {assets_after}")

            assets_created = assets_after - assets_before
            print(f"✨ New assets created: {assets_created}")

            # Check if raw records were marked as processed
            processed_result = await db.execute(
                "SELECT COUNT(*) FROM migration.raw_import_records WHERE master_flow_id = %s AND is_processed = true",
                (existing_flow_id,)
            )
            processed_count = processed_result.scalar()
            print(f"📈 Raw records marked as processed: {processed_count}")

            if result.get('status') == 'completed' and result.get('assets_created', 0) > 0:
                print("✅ SUCCESS: Asset inventory handler worked!")

                # Show some created assets
                sample_assets = await db.execute(
                    "SELECT name, asset_type, hostname FROM migration.assets WHERE master_flow_id = %s LIMIT 3",
                    (existing_flow_id,)
                )
                sample_results = sample_assets.fetchall()
                print("📋 Sample created assets:")
                for asset in sample_results:
                    print(f"   - {asset.name} ({asset.asset_type}) - {asset.hostname}")

            else:
                print("❌ Asset inventory did not complete successfully")
                print(f"   Status: {result.get('status', 'unknown')}")
                print(f"   Error: {result.get('error', 'None')}")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Asset Inventory Test with Existing Data")
    asyncio.run(test_existing_raw_data())
    print("✨ Test completed")

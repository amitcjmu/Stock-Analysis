#!/usr/bin/env python3
"""
Test script to validate asset inventory handler implementation
CC: Tests the newly implemented asset creation pipeline
"""

import asyncio
import sys
import uuid
from datetime import datetime

# Add the backend path so we can import modules
sys.path.insert(0, 'backend')

from app.core.database import AsyncSessionLocal
from app.models.data_import import RawImportRecord
from app.models.asset import Asset
from app.services.flow_configs.discovery_handlers import asset_inventory


async def test_asset_inventory_handler():
    """Test the asset inventory handler with mock data"""
    print("🧪 Testing Asset Inventory Handler")

    # Create test flow context
    test_flow_id = str(uuid.uuid4())
    test_client_id = str(uuid.uuid4())
    test_engagement_id = str(uuid.uuid4())

    async with AsyncSessionLocal() as db:
        try:
            # Create a test raw import record
            test_raw_record = RawImportRecord(
                id=uuid.uuid4(),
                master_flow_id=uuid.UUID(test_flow_id),
                client_account_id=uuid.UUID(test_client_id),
                engagement_id=uuid.UUID(test_engagement_id),
                data_import_id=uuid.uuid4(),
                row_number=1,
                raw_data={
                    "name": "test-server-001",
                    "hostname": "test-server-001.example.com",
                    "ip_address": "10.0.1.100",
                    "operating_system": "Ubuntu 20.04",
                    "cpu_cores": "4",
                    "memory_gb": "16",
                    "asset_type": "Server",
                    "environment": "Production",
                    "business_owner": "IT Team"
                }
            )

            db.add(test_raw_record)
            await db.commit()
            print(f"✅ Created test raw record: {test_raw_record.id}")

            # Create mock context
            class MockContext:
                def __init__(self, client_id, engagement_id):
                    self.client_account_id = client_id
                    self.engagement_id = engagement_id
                    self.user_id = "test-user"
                    self.db_session = db

            context = MockContext(test_client_id, test_engagement_id)

            # Prepare phase input
            phase_input = {
                "master_flow_id": test_flow_id,
                "client_account_id": test_client_id,
                "engagement_id": test_engagement_id,
            }

            # Execute the asset inventory handler
            print(f"🔄 Executing asset inventory for flow: {test_flow_id}")
            result = await asset_inventory(
                flow_id=test_flow_id,
                phase_input=phase_input,
                context=context,
                db_session=db
            )

            print(f"📊 Handler result: {result}")

            # Check if assets were created
            assets_query = await db.execute(
                "SELECT COUNT(*) FROM migration.assets WHERE master_flow_id = %s",
                (test_flow_id,)
            )
            assets_count = assets_query.scalar()

            print(f"🎯 Assets created: {assets_count}")

            if result.get('assets_created', 0) > 0:
                print("✅ SUCCESS: Asset inventory handler created assets!")
            else:
                print("❌ FAILURE: No assets were created")
                print(f"   Error: {result.get('error', 'Unknown')}")

            # Cleanup test data
            await db.execute(
                "DELETE FROM migration.assets WHERE master_flow_id = %s",
                (test_flow_id,)
            )
            await db.execute(
                "DELETE FROM migration.raw_import_records WHERE master_flow_id = %s",
                (test_flow_id,)
            )
            await db.commit()
            print("🧹 Cleaned up test data")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            # Cleanup on error
            try:
                await db.rollback()
                await db.execute(
                    "DELETE FROM migration.assets WHERE master_flow_id = %s",
                    (test_flow_id,)
                )
                await db.execute(
                    "DELETE FROM migration.raw_import_records WHERE master_flow_id = %s",
                    (test_flow_id,)
                )
                await db.commit()
            except:
                pass


if __name__ == "__main__":
    print("🚀 Starting Asset Inventory Handler Test")
    asyncio.run(test_asset_inventory_handler())
    print("✨ Test completed")

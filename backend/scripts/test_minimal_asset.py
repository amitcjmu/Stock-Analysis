#!/usr/bin/env python3
"""
Test script for Asset model.
Tests basic CRUD operations with only essential fields.
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


from app.core.database import AsyncSessionLocal
from app.models.asset import (
    Asset,
    AssetStatus,
    AssetType,
    SixRStrategy,
)


async def test_minimal_asset_creation():
    """Test creating a minimal asset record with only essential fields."""

    print("🧪 Testing Asset model...")

    async with AsyncSessionLocal() as db:
        try:
            # Create a test asset with minimal required fields
            test_asset = Asset(
                migration_id=1,  # Assuming migration ID 1 exists
                name="test-asset-minimal",
                asset_type=AssetType.SERVER,
                description="Test asset for minimal model validation",
                hostname="test-host-minimal",
                ip_address="192.168.1.100",
                discovery_status="discovered",
                mapping_status="pending",
                cleanup_status="pending",
                assessment_readiness="not_ready",
            )

            print(f"✅ Created Asset object: {test_asset}")

            # Add to database
            db.add(test_asset)
            await db.commit()
            await db.refresh(test_asset)

            print(f"✅ Successfully inserted Asset with ID: {test_asset.id}")
            print(f"   Name: {test_asset.name}")
            print(f"   Type: {test_asset.asset_type}")
            print(f"   Status: {test_asset.status}")
            print(f"   Discovery Status: {test_asset.discovery_status}")

            # Test reading the asset
            retrieved_asset = await db.get(Asset, test_asset.id)
            if retrieved_asset:
                print(f"✅ Successfully retrieved asset: {retrieved_asset.name}")
                print(f"   Asset dict: {retrieved_asset.to_dict()}")
            else:
                print("❌ Failed to retrieve asset")
                return False

            # Test updating the asset
            retrieved_asset.description = "Updated description for minimal test"
            retrieved_asset.status = AssetStatus.ASSESSED
            await db.commit()

            print("✅ Successfully updated asset")

            # Test querying assets
            from sqlalchemy import select

            result = await db.execute(
                select(Asset).where(Asset.name.like("test-asset%"))
            )
            assets = result.scalars().all()
            print(f"✅ Found {len(assets)} test assets")

            # Clean up - delete the test asset
            await db.delete(retrieved_asset)
            await db.commit()
            print("✅ Successfully deleted test asset")

            return True

        except Exception as e:
            print(f"❌ Error during Asset testing: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback

            traceback.print_exc()
            return False


async def test_workflow_status_fields():
    """Test the workflow status fields specifically."""

    print("\n🧪 Testing workflow status fields...")

    async with AsyncSessionLocal() as db:
        try:
            # Create asset with different workflow statuses
            test_asset = Asset(
                migration_id=1,
                name="test-workflow-asset",
                asset_type=AssetType.APPLICATION,
                discovery_status="completed",
                mapping_status="in_progress",
                cleanup_status="pending",
                assessment_readiness="partial",
            )

            db.add(test_asset)
            await db.commit()
            await db.refresh(test_asset)

            print("✅ Created asset with workflow statuses:")
            print(f"   Discovery: {test_asset.discovery_status}")
            print(f"   Mapping: {test_asset.mapping_status}")
            print(f"   Cleanup: {test_asset.cleanup_status}")
            print(f"   Assessment: {test_asset.assessment_readiness}")

            # Clean up
            await db.delete(test_asset)
            await db.commit()

            return True

        except Exception as e:
            print(f"❌ Error testing workflow fields: {str(e)}")
            return False


async def test_enum_fields():
    """Test the enum fields specifically."""

    print("\n🧪 Testing enum fields...")

    async with AsyncSessionLocal() as db:
        try:
            # Test all enum combinations
            test_combinations = [
                (
                    AssetType.SERVER,
                    AssetStatus.DISCOVERED,
                    SixRStrategy.REHOST,
                ),
                (
                    AssetType.DATABASE,
                    AssetStatus.ASSESSED,
                    SixRStrategy.REPLATFORM,
                ),
                (
                    AssetType.APPLICATION,
                    AssetStatus.PLANNED,
                    SixRStrategy.REFACTOR,
                ),
            ]

            created_assets = []

            for i, (asset_type, status, strategy) in enumerate(test_combinations):
                test_asset = Asset(
                    migration_id=1,
                    name=f"test-enum-{i}",
                    asset_type=asset_type,
                    status=status,
                    six_r_strategy=strategy,
                )

                db.add(test_asset)
                await db.commit()
                await db.refresh(test_asset)
                created_assets.append(test_asset)

                print(
                    f"✅ Created asset with enums: {asset_type.value}, {status.value}, {strategy.value}"
                )

            # Clean up all test assets
            for asset in created_assets:
                await db.delete(asset)
            await db.commit()

            return True

        except Exception as e:
            print(f"❌ Error testing enum fields: {str(e)}")
            return False


async def main():
    """Run all tests."""
    print("🚀 Starting Asset CRUD tests...")

    tests = [test_minimal_asset_creation, test_workflow_status_fields, test_enum_fields]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All Asset tests passed! Database model alignment is working.")
        return True
    else:
        print("❌ Some tests failed. Model-database alignment needs more work.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

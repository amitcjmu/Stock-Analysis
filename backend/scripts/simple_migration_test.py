#!/usr/bin/env python3
"""
Simple test script to verify the new Asset model can create records.
Tests the database migration and model functionality.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.asset import Asset, AssetType, AssetStatus

async def test_asset_creation():
    """Test creating a simple asset record with existing columns only."""
    
    async with AsyncSessionLocal() as db:
        # Create a test asset with only existing columns
        test_asset = Asset(
            name="Test Server",
            hostname="test-server-01",
            asset_type=AssetType.SERVER,
            status=AssetStatus.DISCOVERED,
            description="Test asset for migration verification",
            operating_system="Ubuntu 20.04",
            environment="test",
            # Only use columns that exist
            discovery_status="completed",
            mapping_status="pending", 
            cleanup_status="pending",
            assessment_readiness="not_ready",
            completeness_score=60.0,
            quality_score=70.0,
            source_system="migration_test"
        )
        
        db.add(test_asset)
        await db.commit()
        await db.refresh(test_asset)
        
        print(f"✅ Successfully created test asset: {test_asset.name} (ID: {test_asset.id})")
        
        # Test querying
        query_result = await db.get(Asset, test_asset.id)
        print(f"✅ Successfully queried asset: {query_result.name}")
        
        return test_asset.id

async def main():
    """Main test function."""
    print("🧪 Testing Asset model and database migration...")
    
    try:
        asset_id = await test_asset_creation()
        print(f"✅ Asset model test completed successfully! Asset ID: {asset_id}")
        
        # Test workflow readiness calculation
        async with AsyncSessionLocal() as db:
            asset = await db.get(Asset, asset_id)
            readiness_score = asset.get_migration_readiness_score()
            print(f"✅ Migration readiness score: {readiness_score}")
        
    except Exception as e:
        print(f"❌ Asset model test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1) 
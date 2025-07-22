#!/usr/bin/env python3
"""
Debug script to investigate Asset Inventory API issues.
"""

import asyncio
import json

import aiohttp


async def test_asset_inventory_api():
    """Test the Asset Inventory API endpoints to identify the 500 error."""
    
    print("🔍 Testing Asset Inventory API endpoints...")
    
    base_url = "http://localhost:8000"
    endpoints_to_test = [
        "/api/v1/discovery/assets",
        "/api/v1/discovery/assets?page=1&page_size=10",
        "/api/v1/discovery/assets/discovery-metrics",
        "/api/v1/discovery/assets/health"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints_to_test:
            try:
                print(f"\n🧪 Testing: {endpoint}")
                async with session.get(f"{base_url}{endpoint}") as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Success: {json.dumps(result, indent=2)[:500]}...")
                    else:
                        error_text = await response.text()
                        print(f"❌ Error: {error_text}")
                        
            except Exception as e:
                print(f"❌ Exception testing {endpoint}: {e}")

async def test_database_cmdb_assets():
    """Test direct database access to cmdb_assets table."""
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        
        print("\n🔍 Testing direct database access to cmdb_assets...")
        
        async with AsyncSessionLocal() as session:
            # Test basic table existence
            print("\n1. Checking if cmdb_assets table exists:")
            table_check = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'cmdb_assets'
            """))
            tables = table_check.fetchall()
            if tables:
                print("✅ cmdb_assets table exists")
            else:
                print("❌ cmdb_assets table does not exist!")
                return
            
            # Test table columns
            print("\n2. Checking cmdb_assets table columns:")
            columns_check = await session.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'cmdb_assets'
                ORDER BY ordinal_position
            """))
            columns = columns_check.fetchall()
            print("Available columns:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            
            # Test basic select
            print("\n3. Testing basic SELECT query:")
            try:
                count_check = await session.execute(text("SELECT COUNT(*) FROM cmdb_assets"))
                count = count_check.scalar()
                print(f"✅ Total records in cmdb_assets: {count}")
                
                if count > 0:
                    # Get sample data
                    sample_check = await session.execute(text("SELECT id, name, hostname, asset_type FROM cmdb_assets LIMIT 3"))
                    samples = sample_check.fetchall()
                    print("Sample records:")
                    for sample in samples:
                        print(f"  - {sample[0]}: {sample[1]} ({sample[2]}) - {sample[3]}")
                        
            except Exception as e:
                print(f"❌ Error in basic SELECT: {e}")
            
            # Test context-aware columns
            print("\n4. Checking for context columns:")
            context_columns = ['client_account_id', 'engagement_id', 'session_id']
            for col in context_columns:
                try:
                    context_check = await session.execute(text(f"SELECT COUNT(*) FROM cmdb_assets WHERE {col} IS NOT NULL"))
                    non_null_count = context_check.scalar()
                    print(f"✅ {col}: {non_null_count} non-null records")
                except Exception as e:
                    print(f"❌ {col} column issue: {e}")
                    
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

async def test_asset_model_import():
    """Test importing the CMDBAsset model."""
    try:
        print("\n🔍 Testing CMDBAsset model import...")
        from app.models.cmdb_asset import AssetStatus, AssetType, CMDBAsset, SixRStrategy
        print("✅ Successfully imported CMDBAsset model")
        
        # Test enum values
        print(f"AssetType values: {[e.value for e in AssetType]}")
        print(f"AssetStatus values: {[e.value for e in AssetStatus]}")
        print(f"SixRStrategy values: {[e.value for e in SixRStrategy]}")
        
    except Exception as e:
        print(f"❌ Failed to import CMDBAsset model: {e}")

async def main():
    """Run all debug tests."""
    print("🧪 Asset Inventory Debug Analysis")
    print("=" * 50)
    
    # Test 1: Model imports
    await test_asset_model_import()
    
    # Test 2: Direct database access
    await test_database_cmdb_assets()
    
    # Test 3: API endpoints
    await test_asset_inventory_api()
    
    print("\n" + "=" * 50)
    print("🏁 Debug analysis complete!")

if __name__ == "__main__":
    asyncio.run(main()) 
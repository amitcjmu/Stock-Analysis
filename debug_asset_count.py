import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append('backend')

async def check_asset_count():
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.cmdb_asset import CMDBAsset
        from sqlalchemy import select, func
        
        print("🔍 Checking asset count in database...")
        
        async with AsyncSessionLocal() as session:
            # Get total count
            result = await session.execute(select(func.count(CMDBAsset.id)))
            total_count = result.scalar()
            print(f"📊 Total assets in database: {total_count}")
            
            # Get first 5 assets for verification
            result = await session.execute(select(CMDBAsset).limit(5))
            assets = result.scalars().all()
            
            print(f"📋 Sample assets:")
            for asset in assets:
                print(f"  - {asset.hostname} ({asset.asset_type})")
                
            # Check asset types
            result = await session.execute(
                select(CMDBAsset.asset_type, func.count(CMDBAsset.id))
                .group_by(CMDBAsset.asset_type)
            )
            type_counts = result.all()
            
            print(f"📈 Asset type breakdown:")
            for asset_type, count in type_counts:
                print(f"  - {asset_type}: {count}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_asset_count()) 
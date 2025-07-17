"""
Test script to verify asset uniqueness constraints are working
"""

import asyncio
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset


async def test_duplicate_hostname_constraint():
    """Test that duplicate hostnames are prevented"""
    client_id = uuid.UUID("21990f3a-abb6-4862-be06-cb6f854e167b")
    engagement_id = uuid.UUID("58467010-6a72-44e8-ba37-cc0238724455")
    
    async with AsyncSessionLocal() as db:
        # Create first asset
        asset1 = Asset(
            client_account_id=client_id,
            engagement_id=engagement_id,
            name="Test Asset 1",
            asset_name="Test Asset 1",
            hostname="test-server-001",
            asset_type="server",
            status="discovered",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(asset1)
        await db.commit()
        
        # Try to create duplicate with same hostname
        asset2 = Asset(
            client_account_id=client_id,
            engagement_id=engagement_id,
            name="Different Name",
            asset_name="Different Name", 
            hostname="test-server-001",  # Same hostname
            asset_type="server",
            status="discovered",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(asset2)
        
        try:
            await db.commit()
            print("❌ ERROR: Duplicate hostname was allowed!")
            return False
        except IntegrityError as e:
            await db.rollback()
            print("✅ SUCCESS: Duplicate hostname was prevented")
            print(f"   Error: {str(e.orig)}")
            
            # Clean up the test asset
            await db.delete(asset1)
            await db.commit()
            return True


async def test_duplicate_name_constraint():
    """Test that duplicate names are prevented"""
    client_id = uuid.UUID("21990f3a-abb6-4862-be06-cb6f854e167b")
    engagement_id = uuid.UUID("58467010-6a72-44e8-ba37-cc0238724455")
    
    async with AsyncSessionLocal() as db:
        # Create first asset
        asset1 = Asset(
            client_account_id=client_id,
            engagement_id=engagement_id,
            name="Unique Application",
            asset_name="Unique Application",
            asset_type="application",
            status="discovered",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(asset1)
        await db.commit()
        
        # Try to create duplicate with same name
        asset2 = Asset(
            client_account_id=client_id,
            engagement_id=engagement_id,
            name="Unique Application",  # Same name
            asset_name="Unique Application",
            asset_type="application",
            status="discovered",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(asset2)
        
        try:
            await db.commit()
            print("❌ ERROR: Duplicate name was allowed!")
            return False
        except IntegrityError as e:
            await db.rollback()
            print("✅ SUCCESS: Duplicate name was prevented")
            print(f"   Error: {str(e.orig)}")
            
            # Clean up the test asset
            await db.delete(asset1)
            await db.commit()
            return True


async def main():
    """Run all constraint tests"""
    print("🧪 Testing Asset Uniqueness Constraints")
    print("=" * 50)
    
    # Test hostname constraint
    print("\n1. Testing hostname uniqueness constraint:")
    await test_duplicate_hostname_constraint()
    
    # Test name constraint
    print("\n2. Testing name uniqueness constraint:")
    await test_duplicate_name_constraint()
    
    print("\n✅ All constraint tests completed!")


if __name__ == "__main__":
    import os
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"
    asyncio.run(main())
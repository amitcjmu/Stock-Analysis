"""
Simple test to debug collection flow creation
"""
import asyncio
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import User
from app.models.collection_flow import AutomationTier, CollectionFlow, CollectionFlowStatus, CollectionPhase


async def test_create_collection_flow():
    async with AsyncSessionLocal() as db:
        try:
            # Get demo user
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.email == "demo@demo-corp.com"))
            user = result.scalar_one_or_none()
            
            if not user:
                print("Demo user not found!")
                return
                
            print(f"Found user: {user.id}")
            
            # Create collection flow
            flow_id = uuid.uuid4()
            collection_flow = CollectionFlow(
                flow_id=flow_id,
                flow_name=f"Test Collection Flow - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                user_id=user.id,
                created_by=user.id,
                status=CollectionFlowStatus.INITIALIZED.value,
                automation_tier=AutomationTier.TIER_2.value,
                collection_config={},
                current_phase=CollectionPhase.INITIALIZATION.value
            )
            
            print("Adding collection flow to database...")
            db.add(collection_flow)
            
            print("Committing...")
            await db.commit()
            
            print(f"✅ Collection flow created successfully: {collection_flow.id}")
            
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    print("Testing collection flow creation...")
    asyncio.run(test_create_collection_flow())
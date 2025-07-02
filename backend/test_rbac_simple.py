#!/usr/bin/env python3
"""
Simple test to verify RBAC auto-mapping works with proper database connection
"""

import asyncio
import os
from app.core.database import get_db, AsyncSessionLocal
from app.models import User, ClientAccount, Engagement
from app.models.rbac import ClientAccess, EngagementAccess
from sqlalchemy import select, cast, String


async def test_rbac():
    print("🔍 Testing RBAC Auto-Mapping...")
    print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not set')}")
    
    try:
        async with AsyncSessionLocal() as db:
            # Find demo client
            client_result = await db.execute(
                select(ClientAccount).where(
                    cast(ClientAccount.id, String).like('%def0-def0-def0%')
                )
            )
            demo_client = client_result.scalar_one_or_none()
            
            if demo_client:
                print(f"✅ Found demo client: {demo_client.name} ({demo_client.id})")
                
                # Check ClientAccess records
                access_result = await db.execute(
                    select(ClientAccess).where(
                        ClientAccess.client_account_id == demo_client.id
                    ).limit(5)
                )
                accesses = access_result.scalars().all()
                
                print(f"\n📋 Found {len(accesses)} ClientAccess records for this client:")
                for access in accesses:
                    user_profile = await db.get(User, access.user_profile_id)
                    if user_profile:
                        print(f"  - User: {user_profile.email}, Access Level: {access.access_level}, Active: {access.is_active}")
                
                # Find demo engagement
                engagement_result = await db.execute(
                    select(Engagement).where(
                        Engagement.client_account_id == demo_client.id,
                        cast(Engagement.id, String).like('%def0-def0-def0%')
                    ).limit(1)
                )
                demo_engagement = engagement_result.scalar_one_or_none()
                
                if demo_engagement:
                    print(f"\n✅ Found demo engagement: {demo_engagement.name} ({demo_engagement.id})")
                    
                    # Check EngagementAccess records
                    eng_access_result = await db.execute(
                        select(EngagementAccess).where(
                            EngagementAccess.engagement_id == demo_engagement.id
                        ).limit(5)
                    )
                    eng_accesses = eng_access_result.scalars().all()
                    
                    print(f"\n📋 Found {len(eng_accesses)} EngagementAccess records for this engagement:")
                    for access in eng_accesses:
                        user_profile = await db.get(User, access.user_profile_id)
                        if user_profile:
                            print(f"  - User: {user_profile.email}, Role: {access.engagement_role}, Active: {access.is_active}")
                else:
                    print("❌ No demo engagement found")
            else:
                print("❌ No demo client found")
                
                # List all clients
                all_clients = await db.execute(select(ClientAccount).limit(5))
                clients = all_clients.scalars().all()
                print("\n📋 Available clients:")
                for client in clients:
                    print(f"  - {client.name} ({client.id})")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_rbac())
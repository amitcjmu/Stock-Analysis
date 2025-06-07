#!/usr/bin/env python3
"""
Check Real Clients and Engagements for Multi-Tenant Testing
"""

import asyncio
import sys
sys.path.append('/app')

from app.models.client_account import ClientAccount
from app.core.database import AsyncSessionLocal
from sqlalchemy import select

async def check_clients_and_engagements():
    print("🏢 Checking Real Clients and Engagements")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        # Get all client accounts
        client_result = await session.execute(select(ClientAccount))
        clients = client_result.scalars().all()
        
        print(f"\n📊 Found {len(clients)} Client Accounts:")
        
        real_clients = []
        demo_clients = []
        
        for client in clients:
            client_info = {
                "id": str(client.id),
                "name": client.name,
                "slug": client.slug,
                "is_mock": client.is_mock,
                "industry": client.industry,
                "created_at": client.created_at.isoformat() if client.created_at else None
            }
            
            if client.is_mock:
                demo_clients.append(client_info)
                print(f"  🎭 DEMO: {client.name} ({client.id}) - {client.slug}")
            else:
                real_clients.append(client_info)
                print(f"  🏢 REAL: {client.name} ({client.id}) - {client.slug}")
        
        print(f"\n📈 Summary:")
        print(f"  Real Clients: {len(real_clients)}")
        print(f"  Demo Clients: {len(demo_clients)}")
        
        # Check if engagement model exists
        try:
            from app.models.engagement import Engagement
            engagement_result = await session.execute(select(Engagement))
            engagements = engagement_result.scalars().all()
            
            print(f"\n🎯 Found {len(engagements)} Engagements:")
            for engagement in engagements:
                print(f"  📝 {engagement.name} (Client: {engagement.client_account_id}, ID: {engagement.id})")
                
        except ImportError:
            print("\n⚠️ Engagement model not available")
        
        # Recommend clients for testing
        print(f"\n🧪 Recommended for End-to-End Testing:")
        for client in real_clients:
            print(f"  ✅ Use Client: {client['name']} (ID: {client['id']})")
        
        if not real_clients:
            print("  ❌ No real clients found - need to create real clients for testing")
            
        return real_clients, demo_clients

if __name__ == "__main__":
    asyncio.run(check_clients_and_engagements()) 
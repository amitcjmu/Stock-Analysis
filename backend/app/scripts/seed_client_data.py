#!/usr/bin/env python3
"""
Data seeding script to ensure client accounts have proper industry and company_size values.
This script should be run after migrations to populate required fields.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import uuid

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.client_account import ClientAccount


async def seed_client_data():
    """Seed client account data with proper industry and company_size values."""
    
    async with AsyncSessionLocal() as session:
        try:
            # Get all client accounts with NULL or empty industry/company_size
            result = await session.execute(
                select(ClientAccount).where(
                    (ClientAccount.industry.is_(None)) |
                    (ClientAccount.industry == '') |
                    (ClientAccount.company_size.is_(None)) |
                    (ClientAccount.company_size == '')
                )
            )
            
            clients_to_update = result.scalars().all()
            
            if not clients_to_update:
                print("✅ All client accounts already have proper industry and company_size values")
                return
            
            print(f"🔧 Found {len(clients_to_update)} client accounts that need industry/company_size updates")
            
            # Update each client with appropriate values
            for client in clients_to_update:
                industry = "Technology"  # Default industry
                company_size = "Medium"  # Default company size
                
                # Set specific values based on client name patterns
                if "AI Modernize" in client.name or "Platform" in client.name:
                    company_size = "Enterprise"
                elif "Test" in client.name or "Demo" in client.name:
                    company_size = "Medium"
                elif "Enterprise" in client.name or "Corp" in client.name:
                    company_size = "Large"
                elif "Small" in client.name or "Startup" in client.name:
                    company_size = "Small"
                
                # Update the client
                await session.execute(
                    update(ClientAccount)
                    .where(ClientAccount.id == client.id)
                    .values(
                        industry=industry,
                        company_size=company_size
                    )
                )
                
                print(f"  ✅ Updated '{client.name}': industry='{industry}', company_size='{company_size}'")
            
            await session.commit()
            print(f"🎉 Successfully updated {len(clients_to_update)} client accounts")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding client data: {e}")
            raise

async def create_default_clients_if_missing():
    """Create default client accounts if none exist."""
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if any client accounts exist
            result = await session.execute(select(ClientAccount).limit(1))
            existing_client = result.scalar_one_or_none()
            
            if existing_client:
                print("✅ Client accounts already exist, skipping default creation")
                return
            
            print("🔧 Creating default client accounts...")
            
            # Create AI Modernize Platform client
            ai_force_client = ClientAccount(
                id=uuid.uuid4(),
                name="AI Modernize Platform",
                industry="Technology",
                company_size="Enterprise",
                description="Platform administration client account",
                slug="ai-force-platform",
                is_active=True,
                business_objectives=[],
                it_guidelines={},
                decision_criteria={},
                agent_preferences={},
                target_cloud_providers=[],
                business_priorities=[],
                compliance_requirements=[]
            )
            
            # Create Test Corporation client
            test_client = ClientAccount(
                id=uuid.uuid4(),
                name="Test Corporation",
                industry="Technology", 
                company_size="Medium",
                description="Test client for development and validation",
                slug="test-corporation",
                is_active=True,
                business_objectives=[],
                it_guidelines={},
                decision_criteria={},
                agent_preferences={},
                target_cloud_providers=[],
                business_priorities=[],
                compliance_requirements=[]
            )
            
            session.add(ai_force_client)
            session.add(test_client)
            await session.commit()
            
            print("  ✅ Created 'AI Modernize Platform' client")
            print("  ✅ Created 'Test Corporation' client")
            print("🎉 Successfully created default client accounts")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating default clients: {e}")
            raise

async def main():
    """Main seeding function."""
    print("🌱 Starting client data seeding...")
    
    # First, create default clients if none exist
    await create_default_clients_if_missing()
    
    # Then, ensure all clients have proper industry/company_size values
    await seed_client_data()
    
    print("✅ Client data seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 
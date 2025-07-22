#!/usr/bin/env python3
"""
Create additional demo clients and engagements for testing platform admin access
"""
import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.client_account import ClientAccount, Engagement


async def create_additional_demo_data():
    """Create additional test clients and engagements"""
    async with AsyncSessionLocal() as db:
        print("Creating additional demo clients and engagements...")
        
        # Define additional clients
        additional_clients = [
            {
                "id": uuid.uuid4(),
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Large enterprise client specializing in manufacturing",
                "industry": "Manufacturing",
                "company_size": "1000-5000",
                "headquarters_location": "New York, USA",
                "primary_contact_name": "John Smith",
                "primary_contact_email": "john.smith@acme.com",
                "primary_contact_phone": "+1-555-0100",
                "subscription_tier": "enterprise",
                "billing_contact_email": "billing@acme.com",
                "settings": {
                    "migration_preferences": {
                        "target_clouds": ["aws", "azure"],
                        "preferred_migration_window": "Q2 2025",
                        "budget_range": "5M-10M"
                    }
                },
                "business_objectives": {
                    "primary_goals": ["Cost optimization", "Modernization", "Global scalability"],
                    "compliance_requirements": ["SOC2", "ISO27001", "GDPR"]
                }
            },
            {
                "id": uuid.uuid4(),
                "name": "TechCorp Industries",
                "slug": "techcorp",
                "description": "Technology company focused on SaaS solutions",
                "industry": "Technology",
                "company_size": "500-1000",
                "headquarters_location": "San Francisco, USA",
                "primary_contact_name": "Sarah Johnson",
                "primary_contact_email": "sarah@techcorp.com",
                "primary_contact_phone": "+1-555-0200",
                "subscription_tier": "professional",
                "billing_contact_email": "finance@techcorp.com",
                "settings": {
                    "migration_preferences": {
                        "target_clouds": ["gcp"],
                        "preferred_migration_window": "Q3 2025",
                        "budget_range": "2M-5M"
                    }
                },
                "business_objectives": {
                    "primary_goals": ["Innovation", "Speed to market", "Developer productivity"],
                    "compliance_requirements": ["PCI-DSS", "HIPAA"]
                }
            },
            {
                "id": uuid.uuid4(),
                "name": "Global Enterprises",
                "slug": "global-enterprises",
                "description": "Multinational conglomerate with diverse business units",
                "industry": "Conglomerate",
                "company_size": "10000+",
                "headquarters_location": "London, UK",
                "primary_contact_name": "Michael Brown",
                "primary_contact_email": "m.brown@globalent.com",
                "primary_contact_phone": "+44-20-5555-0300",
                "subscription_tier": "enterprise",
                "billing_contact_email": "accounts@globalent.com",
                "settings": {
                    "migration_preferences": {
                        "target_clouds": ["aws", "azure", "gcp"],
                        "preferred_migration_window": "2025-2027",
                        "budget_range": "50M+"
                    }
                },
                "business_objectives": {
                    "primary_goals": ["Digital transformation", "Business unit autonomy", "Risk mitigation"],
                    "compliance_requirements": ["SOX", "GDPR", "Regional compliance"]
                }
            }
        ]
        
        # Create clients
        created_clients = []
        for client_data in additional_clients:
            # Check if client already exists
            existing = await db.get(ClientAccount, client_data["id"])
            if not existing:
                client = ClientAccount(**client_data)
                db.add(client)
                created_clients.append(client)
                print(f"  ✅ Created client: {client.name}")
            else:
                created_clients.append(existing)
                print(f"  ℹ️  Client already exists: {existing.name}")
        
        await db.commit()
        
        # Create engagements for each client
        engagement_types = ["migration", "assessment", "optimization"]
        statuses = ["planning", "active", "active", "completed"]
        
        for i, client in enumerate(created_clients):
            # Create 2-3 engagements per client
            num_engagements = 2 if i == 0 else 3
            
            for j in range(num_engagements):
                engagement_data = {
                    "id": uuid.uuid4(),
                    "client_account_id": client.id,
                    "name": f"{client.name} - {['Cloud Migration', 'Infrastructure Assessment', 'Cost Optimization'][j]}",
                    "slug": f"{client.slug}-engagement-{j+1}",
                    "description": f"Engagement {j+1} for {client.name}",
                    "status": statuses[j % len(statuses)],
                    "engagement_type": engagement_types[j % len(engagement_types)],
                    "start_date": datetime.now() - timedelta(days=30 * (3 - j)),
                    "target_completion_date": datetime.now() + timedelta(days=180 + 90 * j),
                    "settings": {
                        "priority": ["high", "medium", "low"][j % 3],
                        "team_size": 5 + j * 2
                    },
                    "metadata": {
                        "workloads": 20 + j * 10,
                        "applications": 10 + j * 5,
                        "estimated_duration_months": 6 + j * 3
                    }
                }
                
                # Check if engagement already exists
                existing = await db.get(Engagement, engagement_data["id"])
                if not existing:
                    engagement = Engagement(**engagement_data)
                    db.add(engagement)
                    print(f"    ✅ Created engagement: {engagement.name}")
                else:
                    print(f"    ℹ️  Engagement already exists: {existing.name}")
        
        await db.commit()
        
        # Verify counts
        from sqlalchemy import func, select
        
        client_count = await db.execute(select(func.count()).select_from(ClientAccount))
        engagement_count = await db.execute(select(func.count()).select_from(Engagement))
        
        print("\n📊 Final counts:")
        print(f"  - Total clients: {client_count.scalar_one()}")
        print(f"  - Total engagements: {engagement_count.scalar_one()}")
        
        print("\n✅ Additional demo data created successfully!")


if __name__ == "__main__":
    asyncio.run(create_additional_demo_data())
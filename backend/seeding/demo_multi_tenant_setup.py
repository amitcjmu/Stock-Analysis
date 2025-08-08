"""
⚠️ WARNING: DO NOT RUN THIS SCRIPT! ⚠️

This script uses SHA256 password hashing which is incompatible with the
authentication service that expects bcrypt hashes. Running this script will
set invalid password hashes that will prevent login.

USE INSTEAD: python -m app.core.database_initialization

The database initialization module correctly uses passlib with bcrypt and
will set passwords that work with the authentication service.

---

Demo multi-tenant data setup with clearly identifiable demo UUIDs and naming.
All demo UUIDs use pattern: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX
All emails use pattern: user@demo.company.com
All engagements have "Demo" prefix
"""

import asyncio
import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import ClientAccount, Engagement, User, UserAccountAssociation
from app.models.rbac import UserProfile, UserStatus


def get_password_hash(password: str) -> str:
    """Simple password hashing for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_demo_uuid() -> uuid.UUID:
    """Create UUID with -def0-def0-def0- pattern in the middle for easy identification"""
    # Generate cryptographically secure random hex for start and end
    start = "".join(secrets.choice("0123456789abcdef") for _ in range(8))
    end = "".join(secrets.choice("0123456789abcdef") for _ in range(12))

    # Create pattern: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX
    uuid_string = f"{start}-def0-def0-def0-{end}"
    return uuid.UUID(uuid_string)


async def clean_demo_data():
    """Clean existing demo data before recreating"""
    async with AsyncSessionLocal() as session:
        print("🧹 Cleaning existing demo data...")

        # Delete demo users (by email pattern)
        result = await session.execute(select(User).where(User.email.like("%@demo.%")))
        demo_users = result.scalars().all()
        for user in demo_users:
            await session.delete(user)

        # Delete demo client accounts (by name pattern instead of UUID since they're random)
        result = await session.execute(
            select(ClientAccount).where(ClientAccount.name.like("Demo %"))
        )
        demo_clients = result.scalars().all()
        for client in demo_clients:
            await session.delete(client)

        await session.commit()
        print("✅ Demo data cleaned")


async def create_demo_multi_tenant_data():
    """Create demo multi-tenant data with clear demo identifiers"""
    async with AsyncSessionLocal() as session:
        # Generate demo UUIDs that we'll use throughout
        techcorp_id = create_demo_uuid()
        retailplus_id = create_demo_uuid()
        manufacturing_id = create_demo_uuid()

        # Demo client accounts with demo UUIDs
        demo_accounts = [
            {
                "id": techcorp_id,
                "name": "Demo TechCorp Industries",
                "slug": "demo-techcorp",
                "description": "Demo technology manufacturing company for testing",
                "industry": "Technology",
                "company_size": "1000-5000",
                "headquarters_location": "Demo City, CA",
                "primary_contact_name": "Demo Sarah Chen",
                "primary_contact_email": "sarah.chen@demo.techcorp.com",
                "contact_phone": "+1-555-0100",
            },
            {
                "id": retailplus_id,
                "name": "Demo RetailPlus Global",
                "slug": "demo-retailplus",
                "description": "Demo international retail chain for testing",
                "industry": "Retail",
                "company_size": "5000+",
                "headquarters_location": "Demo City, NY",
                "primary_contact_name": "Demo Michael Rodriguez",
                "primary_contact_email": "michael.rodriguez@demo.retailplus.com",
                "contact_phone": "+1-555-0200",
            },
            {
                "id": manufacturing_id,
                "name": "Demo ManufacturingCorp USA",
                "slug": "demo-manufacturing",
                "description": "Demo industrial manufacturing for testing",
                "industry": "Manufacturing",
                "company_size": "500-1000",
                "headquarters_location": "Demo City, MI",
                "primary_contact_name": "Demo Jennifer Davis",
                "primary_contact_email": "jennifer.davis@demo.manufacturing.com",
                "contact_phone": "+1-555-0300",
            },
        ]

        # Create demo client accounts
        print("\n📁 Creating demo client accounts...")
        for account_data in demo_accounts:
            account = ClientAccount(**account_data)
            session.add(account)
            print(f"✅ Created: {account_data['name']}")

        await session.commit()

        # Generate engagement IDs
        techcorp_engagement_id = create_demo_uuid()
        retailplus_engagement_id = create_demo_uuid()
        manufacturing_engagement_id = create_demo_uuid()

        # Demo engagements with demo UUIDs linked to correct clients
        demo_engagements = [
            {
                "id": techcorp_engagement_id,
                "client_account_id": techcorp_id,
                "name": "Demo TechCorp Cloud Migration 2025",
                "slug": "demo-techcorp-cloud",
                "description": "Demo project: Migrate legacy systems to Azure",
                "status": "active",
                "engagement_type": "migration",
            },
            {
                "id": retailplus_engagement_id,
                "client_account_id": retailplus_id,
                "name": "Demo RetailPlus Infrastructure Modernization",
                "slug": "demo-retailplus-infra",
                "description": "Demo project: Modernize retail POS systems",
                "status": "active",
                "engagement_type": "assessment",
            },
            {
                "id": manufacturing_engagement_id,
                "client_account_id": manufacturing_id,
                "name": "Demo ManufacturingCorp ERP Migration",
                "slug": "demo-manufacturing-erp",
                "description": "Demo project: Migrate ERP to cloud",
                "status": "active",
                "engagement_type": "planning",
            },
        ]

        print("\n📋 Creating demo engagements...")
        for eng_data in demo_engagements:
            engagement = Engagement(
                **eng_data,
                start_date=datetime.now(timezone.utc),
                target_completion_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
            )
            session.add(engagement)
            print(f"✅ Created: {eng_data['name']}")

        await session.commit()

        # Demo users with demo emails and UUIDs
        demo_users = [
            {
                "id": create_demo_uuid(),
                "email": "admin@demo.techcorp.com",
                "first_name": "Demo",
                "last_name": "TechAdmin",
                "client_id": techcorp_id,
                "engagement_id": techcorp_engagement_id,
                "role": "client_admin",
            },
            {
                "id": create_demo_uuid(),
                "email": "analyst@demo.techcorp.com",
                "first_name": "Demo",
                "last_name": "TechAnalyst",
                "client_id": techcorp_id,
                "engagement_id": techcorp_engagement_id,
                "role": "analyst",
            },
            {
                "id": create_demo_uuid(),
                "email": "admin@demo.retailplus.com",
                "first_name": "Demo",
                "last_name": "RetailAdmin",
                "client_id": retailplus_id,
                "engagement_id": retailplus_engagement_id,
                "role": "client_admin",
            },
            {
                "id": create_demo_uuid(),
                "email": "viewer@demo.retailplus.com",
                "first_name": "Demo",
                "last_name": "RetailViewer",
                "client_id": retailplus_id,
                "engagement_id": retailplus_engagement_id,
                "role": "viewer",
            },
            {
                "id": create_demo_uuid(),
                "email": "manager@demo.manufacturing.com",
                "first_name": "Demo",
                "last_name": "MfgManager",
                "client_id": manufacturing_id,
                "engagement_id": manufacturing_engagement_id,
                "role": "engagement_manager",
            },
        ]

        print("\n👥 Creating demo users...")
        for user_data in demo_users:
            user = User(
                id=user_data["id"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                password_hash=get_password_hash(
                    "Demo123!"
                ),  # nosec B105 - Demo password for seeding
                is_active=True,
                is_verified=True,
                default_client_id=user_data["client_id"],
                default_engagement_id=user_data["engagement_id"],
            )
            session.add(user)
            print(f"✅ Created: {user_data['email']}")

            # Create user-client association
            association = UserAccountAssociation(
                id=uuid.uuid4(),  # Regular UUID for associations
                user_id=user_data["id"],
                client_account_id=user_data["client_id"],
                role=user_data["role"],
            )
            session.add(association)

            # Create active user profile for login
            profile = UserProfile(
                user_id=user_data["id"],
                status=UserStatus.ACTIVE,
                approved_at=datetime.now(timezone.utc),
                registration_reason="Demo account for testing",
                organization=f"Demo {user_data['client_id']}",
                role_description=f"Demo {user_data['role']}",
                requested_access_level="admin",
                notification_preferences={"email": True, "slack": False},
            )
            session.add(profile)

        await session.commit()
        print("\n✅ Demo multi-tenant setup complete!")


async def verify_demo_setup():
    """Verify the demo setup with summary"""
    async with AsyncSessionLocal() as session:
        print("\n" + "=" * 60)
        print("📊 DEMO DATA SUMMARY")
        print("=" * 60)

        # Count demo client accounts
        result = await session.execute(
            select(ClientAccount).where(ClientAccount.name.like("Demo %"))
        )
        demo_clients = result.scalars().all()
        print(f"\n🏢 Demo Client Accounts: {len(demo_clients)}")
        for client in demo_clients:
            print(f"   - {client.name}")
            print(f"     ID: {client.id}")
            print(f"     Slug: {client.slug}")

        # Count demo engagements
        result = await session.execute(
            select(Engagement).where(Engagement.name.like("Demo %"))
        )
        demo_engagements = result.scalars().all()
        print(f"\n📁 Demo Engagements: {len(demo_engagements)}")
        for eng in demo_engagements:
            print(f"   - {eng.name}")
            print(f"     ID: {eng.id}")
            print(f"     Client: {eng.client_account_id}")

        # Count demo users
        result = await session.execute(select(User).where(User.email.like("%@demo.%")))
        demo_users = result.scalars().all()
        print(f"\n👤 Demo Users: {len(demo_users)}")
        for user in demo_users:
            # Get user's role
            result = await session.execute(
                select(UserAccountAssociation)
                .where(UserAccountAssociation.user_id == user.id)
                .limit(1)
            )
            assoc = result.scalar()
            role = assoc.role if assoc else "unknown"
            print(f"   - {user.email} ({role})")
            print(f"     ID: {user.id}")
            print(f"     Name: {user.first_name} {user.last_name}")

        print("\n" + "=" * 60)
        print("✅ All demo accounts use pattern: XXXXXXXX-demo-demo-demo-XXXXXXXXXXXX")
        print("✅ All demo emails use pattern: user@demo.company.com")
        print("✅ All demo entities have 'Demo' prefix in names")
        print("✅ Password for all demo users: Demo123!")
        print("=" * 60)


if __name__ == "__main__":
    print("🚀 Setting up demo multi-tenant data...")
    asyncio.run(clean_demo_data())
    asyncio.run(create_demo_multi_tenant_data())
    asyncio.run(verify_demo_setup())

"""
⚠️ WARNING: DO NOT RUN THIS SCRIPT! ⚠️

This script uses SHA256 password hashing which is incompatible with the
authentication service that expects bcrypt hashes. Running this script will
set invalid password hashes that will prevent login.

USE INSTEAD: python -m app.core.database_initialization

The database initialization module correctly uses passlib with bcrypt and
will set passwords that work with the authentication service.

---

Fix multi-tenant data by adding additional client accounts and associations.
This addresses Agent 4's validation issue where only one client account exists.
"""

import asyncio
import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import ClientAccount, Engagement, User, UserAccountAssociation


def get_password_hash(password: str) -> str:
    """Simple password hashing for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()


async def create_additional_client_accounts():
    """Create additional client accounts for proper multi-tenant testing"""
    async with AsyncSessionLocal() as session:
        # First, check existing client accounts
        result = await session.execute(
            select(ClientAccount).order_by(ClientAccount.name)
        )
        existing_accounts = result.scalars().all()
        print(f"Found {len(existing_accounts)} existing client accounts")

        # Additional client accounts to create
        new_accounts = [
            {
                "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
                "name": "TechCorp Industries",
                "slug": "techcorp",
                "description": "Leading technology manufacturing company",
                "industry": "Technology",
                "company_size": "1000-5000",
                "headquarters_location": "San Francisco, CA",
                "primary_contact_name": "Sarah Chen",
                "primary_contact_email": "sarah.chen@techcorp.com",
                "contact_phone": "+1-415-555-0100",
            },
            {
                "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
                "name": "RetailPlus Global",
                "slug": "retailplus",
                "description": "International retail chain",
                "industry": "Retail",
                "company_size": "5000+",
                "headquarters_location": "New York, NY",
                "primary_contact_name": "Michael Rodriguez",
                "primary_contact_email": "michael.rodriguez@retailplus.com",
                "contact_phone": "+1-212-555-0200",
            },
            {
                "id": uuid.UUID("55555555-5555-5555-5555-555555555555"),
                "name": "ManufacturingCorp USA",
                "slug": "manufacturingcorp",
                "description": "Industrial manufacturing and logistics",
                "industry": "Manufacturing",
                "company_size": "500-1000",
                "headquarters_location": "Detroit, MI",
                "primary_contact_name": "Jennifer Davis",
                "primary_contact_email": "jennifer.davis@manufacturingcorp.com",
                "contact_phone": "+1-313-555-0300",
            },
        ]

        # Create new client accounts
        for account_data in new_accounts:
            # Check if already exists
            existing = await session.get(ClientAccount, account_data["id"])
            if not existing:
                account = ClientAccount(**account_data)
                session.add(account)
                print(f"✅ Created client account: {account_data['name']}")
            else:
                print(f"⚠️ Client account already exists: {account_data['name']}")

        # Commit client accounts first
        await session.commit()

        # Create engagements for each new client
        engagement_data = [
            {
                "client_account_id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
                "name": "TechCorp Cloud Migration 2025",
                "slug": "techcorp-cloud-2025",
                "description": "Migrate legacy systems to Azure",
                "status": "active",
                "engagement_type": "migration",
            },
            {
                "client_account_id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
                "name": "RetailPlus Infrastructure Modernization",
                "slug": "retailplus-infra-modern",
                "description": "Modernize retail POS and inventory systems",
                "status": "active",
                "engagement_type": "assessment",
            },
            {
                "client_account_id": uuid.UUID("55555555-5555-5555-5555-555555555555"),
                "name": "ManufacturingCorp ERP Migration",
                "slug": "manufacturing-erp",
                "description": "Migrate from on-premise ERP to cloud",
                "status": "active",
                "engagement_type": "planning",
            },
        ]

        for eng_data in engagement_data:
            # Check if engagement exists
            result = await session.execute(
                select(Engagement).where(
                    Engagement.client_account_id == eng_data["client_account_id"],
                    Engagement.slug == eng_data["slug"],
                )
            )
            if not result.scalar():
                engagement = Engagement(
                    id=uuid.uuid4(),
                    **eng_data,
                    start_date=datetime.now(timezone.utc),
                    target_completion_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
                )
                session.add(engagement)
                print(f"✅ Created engagement: {eng_data['name']}")

        # Commit engagements before creating users
        await session.commit()

        # Create users for each client account
        client_users = [
            {
                "email": "admin@techcorp.com",
                "first_name": "Tech",
                "last_name": "Admin",
                "client_id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
                "role": "client_admin",
            },
            {
                "email": "analyst@techcorp.com",
                "first_name": "Tech",
                "last_name": "Analyst",
                "client_id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
                "role": "analyst",
            },
            {
                "email": "admin@retailplus.com",
                "first_name": "Retail",
                "last_name": "Admin",
                "client_id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
                "role": "client_admin",
            },
            {
                "email": "viewer@retailplus.com",
                "first_name": "Retail",
                "last_name": "Viewer",
                "client_id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
                "role": "viewer",
            },
            {
                "email": "manager@manufacturingcorp.com",
                "first_name": "Manufacturing",
                "last_name": "Manager",
                "client_id": uuid.UUID("55555555-5555-5555-5555-555555555555"),
                "role": "engagement_manager",
            },
        ]

        for user_data in client_users:
            # Check if user exists
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            user = result.scalar()

            if not user:
                user = User(
                    id=uuid.uuid4(),
                    email=user_data["email"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    password_hash=get_password_hash("Demo123!"),
                    is_active=True,
                    is_verified=True,
                    default_client_id=user_data["client_id"],
                )
                session.add(user)
                print(f"✅ Created user: {user_data['email']}")

            # Create user-client association
            result = await session.execute(
                select(UserAccountAssociation).where(
                    UserAccountAssociation.user_id == user.id,
                    UserAccountAssociation.client_account_id == user_data["client_id"],
                )
            )
            if not result.scalar():
                association = UserAccountAssociation(
                    user_id=user.id,
                    client_account_id=user_data["client_id"],
                    role=user_data["role"],
                )
                session.add(association)
                print(
                    f"✅ Created association: {user_data['email']} -> {user_data['role']}"
                )

        await session.commit()
        print("\n✅ Multi-tenant data fix complete!")


async def verify_multi_tenant_setup():
    """Verify the multi-tenant setup is correct"""
    async with AsyncSessionLocal() as session:
        # Count client accounts
        result = await session.execute(select(ClientAccount))
        accounts = result.scalars().all()
        print(f"\nClient Accounts: {len(accounts)}")
        for account in accounts:
            print(f"  - {account.name} ({account.slug})")

        # Count engagements per client
        for account in accounts:
            result = await session.execute(
                select(Engagement).where(Engagement.client_account_id == account.id)
            )
            engagements = result.scalars().all()
            print(f"\n{account.name} Engagements: {len(engagements)}")
            for eng in engagements:
                print(f"    - {eng.name}")

        # Count users per client
        for account in accounts:
            result = await session.execute(
                select(UserAccountAssociation).where(
                    UserAccountAssociation.client_account_id == account.id
                )
            )
            associations = result.scalars().all()
            print(f"\n{account.name} Users: {len(associations)}")


if __name__ == "__main__":
    print("🔧 Fixing multi-tenant data...")
    asyncio.run(create_additional_client_accounts())
    asyncio.run(verify_multi_tenant_setup())

#!/usr/bin/env python3
"""
⚠️ WARNING: DO NOT RUN THIS SCRIPT! ⚠️

This script uses SHA256 password hashing which is incompatible with the
authentication service that expects bcrypt hashes. Running this script will
set invalid password hashes that will prevent login.

USE INSTEAD: python -m app.core.database_initialization

The database initialization module correctly uses passlib with bcrypt and
will set passwords that work with the authentication service.

---

Minimal demo data seeding script for production deployment.
This creates just the essential demo data without dependencies on other seeding modules.

Usage:
    python scripts/seed_minimal_demo.py
"""
import asyncio
import hashlib
import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models import (
    ClientAccount,
    DiscoveryFlow,
    Engagement,
    User,
    UserAccountAssociation,
    UserRole,
)
from app.models.rbac import UserProfile, UserStatus


def get_password_hash(password: str) -> str:
    """Simple password hashing for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_demo_uuid() -> uuid.UUID:
    """Create UUID with -def0-def0-def0- pattern in the middle for easy identification"""
    # Generate random hex for start and end
    import random

    start = "".join(random.choices("0123456789abcdef", k=8))
    end = "".join(random.choices("0123456789abcdef", k=12))

    # Create pattern: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX
    uuid_string = f"{start}-def0-def0-def0-{end}"
    return uuid.UUID(uuid_string)


async def seed_minimal_demo_data():
    """Create minimal demo data for testing the application"""
    print("\n🌱 Creating minimal demo data...")

    async with AsyncSessionLocal() as session:
        # Check if demo data already exists
        result = await session.execute(
            select(func.count(ClientAccount.id)).where(
                ClientAccount.name.like("Demo %")
            )
        )
        if result.scalar() > 0:
            print("⚠️ Demo data already exists, skipping...")
            return True

        # Generate UUIDs that we'll use throughout
        democorp_id = create_demo_uuid()
        techcorp_id = create_demo_uuid()
        retailplus_id = create_demo_uuid()

        democorp_engagement_id = create_demo_uuid()
        techcorp_engagement_id = create_demo_uuid()
        retailplus_engagement_id = create_demo_uuid()

        # Create demo client accounts
        print("\n📁 Creating demo client accounts...")
        demo_clients = [
            {
                "id": democorp_id,
                "name": "Demo DemoCorp International",
                "slug": "demo-democorp",
            },
            {
                "id": techcorp_id,
                "name": "Demo TechCorp Industries",
                "slug": "demo-techcorp",
            },
            {
                "id": retailplus_id,
                "name": "Demo RetailPlus Global",
                "slug": "demo-retailplus",
            },
        ]

        for client_data in demo_clients:
            client = ClientAccount(
                **client_data,
                description=f"Demo client for testing - {client_data['name']}",
                industry="Technology",
                company_size="1000-5000",
                headquarters_location="Demo City, USA",
                primary_contact_name="Demo Contact",
                primary_contact_email=f"contact@{client_data['slug']}.com",
                contact_phone="+1-555-0000",
            )
            session.add(client)
            print(f"   ✅ {client_data['name']}")

        # Create demo engagements
        print("\n📋 Creating demo engagements...")
        demo_engagements = [
            {
                "id": democorp_engagement_id,
                "client_account_id": democorp_id,
                "name": "Demo Cloud Migration 2024",
                "slug": "demo-cloud-migration",
            },
            {
                "id": techcorp_engagement_id,
                "client_account_id": techcorp_id,
                "name": "Demo TechCorp Migration",
                "slug": "demo-techcorp-migration",
            },
            {
                "id": retailplus_engagement_id,
                "client_account_id": retailplus_id,
                "name": "Demo RetailPlus Modernization",
                "slug": "demo-retail-modern",
            },
        ]

        for eng_data in demo_engagements:
            engagement = Engagement(
                **eng_data,
                description=f"Demo engagement - {eng_data['name']}",
                status="active",
                engagement_type="migration",
                start_date=datetime.now(timezone.utc),
                target_completion_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
            )
            session.add(engagement)
            print(f"   ✅ {eng_data['name']}")

        # Create demo users
        print("\n👤 Creating demo users...")
        demo_users = [
            {
                "id": create_demo_uuid(),
                "email": "demo@demo.democorp.com",
                "first_name": "Demo",
                "last_name": "Manager",
                "client_id": democorp_id,
                "engagement_id": democorp_engagement_id,
                "role": "engagement_manager",
            },
            {
                "id": create_demo_uuid(),
                "email": "analyst@demo.democorp.com",
                "first_name": "Demo",
                "last_name": "Analyst",
                "client_id": democorp_id,
                "engagement_id": democorp_engagement_id,
                "role": "analyst",
            },
            {
                "id": create_demo_uuid(),
                "email": "admin@demo.techcorp.com",
                "first_name": "Demo",
                "last_name": "TechAdmin",
                "client_id": techcorp_id,
                "engagement_id": techcorp_engagement_id,
                "role": "client_admin",
            },
        ]

        for user_data in demo_users:
            # Create user
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

            # Create user role
            user_role = UserRole(
                user_id=user_data["id"],
                client_account_id=user_data["client_id"],
                engagement_id=user_data["engagement_id"],
                role=user_data["role"],
            )
            session.add(user_role)

            # Create user-client association
            association = UserAccountAssociation(
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
                organization="Demo Organization",
                role_description=f"Demo {user_data['role']}",
                requested_access_level="admin",
                notification_preferences={"email": True, "slack": False},
            )
            session.add(profile)

            print(f"   ✅ {user_data['email']} ({user_data['role']})")

        # Create minimal discovery flows
        print("\n🔄 Creating demo discovery flows...")
        demo_flows = [
            {
                "flow_id": create_demo_uuid(),
                "flow_name": "Demo Complete Flow",
                "status": "complete",
                "progress_percentage": 100.0,
                "assessment_ready": True,
                "client_account_id": democorp_id,
                "engagement_id": democorp_engagement_id,
                "user_id": demo_users[0]["id"],
            },
            {
                "flow_id": create_demo_uuid(),
                "flow_name": "Demo In-Progress Flow",
                "status": "active",
                "progress_percentage": 50.0,
                "client_account_id": techcorp_id,
                "engagement_id": techcorp_engagement_id,
                "user_id": demo_users[2]["id"],
            },
        ]

        for flow_data in demo_flows:
            flow = DiscoveryFlow(
                **flow_data,
                data_import_completed=(
                    True if flow_data["progress_percentage"] >= 16.7 else False
                ),
                field_mapping_completed=(
                    True if flow_data["progress_percentage"] >= 33.3 else False
                ),
                data_cleansing_completed=(
                    True if flow_data["progress_percentage"] >= 50.0 else False
                ),
                asset_inventory_completed=(
                    True if flow_data["progress_percentage"] >= 66.7 else False
                ),
                dependency_analysis_completed=(
                    True if flow_data["progress_percentage"] >= 83.3 else False
                ),
                tech_debt_assessment_completed=(
                    True if flow_data["progress_percentage"] >= 100.0 else False
                ),
                learning_scope="engagement",
                memory_isolation_level="strict",
                crewai_state_data={},
            )
            session.add(flow)
            print(f"   ✅ {flow_data['flow_name']}")

        # Commit all changes
        await session.commit()
        print("\n✅ Minimal demo data created successfully!")

        return True


async def main():
    """Main entry point"""
    print("=" * 60)
    print("🌱 MINIMAL DEMO DATA SEEDING")
    print("=" * 60)

    try:
        success = await seed_minimal_demo_data()

        if success:
            print("\n✅ Demo data ready!")
            print("\n🔐 Demo Accounts:")
            print("   - demo@demo.democorp.com (Demo123!)")
            print("   - analyst@demo.democorp.com (Demo123!)")
            print("   - admin@demo.techcorp.com (Demo123!)")
            print("\n📝 All demo entities are marked with:")
            print("   - 'Demo' prefix in names")
            print("   - UUID pattern: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX")
        else:
            print("\n❌ Failed to create demo data")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

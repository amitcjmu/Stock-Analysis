#!/usr/bin/env python3
"""
Script to populate demo data for the AI Modernize Migration Platform.
This script uses the backend API to create demo data, ensuring consistency with application logic.
"""

import asyncio
import sys

sys.path.append("/app")

import uuid
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.demo_constants import (
    DEMO_CLIENT_ID,
    DEMO_CLIENT_NAME,
    DEMO_ENGAGEMENT_ID,
    DEMO_ENGAGEMENT_NAME,
    DEMO_SESSION_ID,
    DEMO_SESSION_NAME,
    DEMO_USER_EMAIL,
    DEMO_USER_ID,
)
from app.models.client_account import ClientAccount, Engagement, User
from app.models.data_import_session import DataImportSession
from app.models.rbac import UserProfile


async def create_demo_users(db: AsyncSession):
    """
    Create demo users - SECURITY HARDENED.
    Only creates legitimate demo user with analyst privileges.
    NO ADMIN DEMO ACCOUNTS ALLOWED.
    """
    print("Creating demo users...")
    print("🔒 SECURITY: Only legitimate demo user (analyst level) will be created")

    # SECURITY: Only create the demo user - no admin@democorp account
    # Demo user - using fixed UUID from system design
    demo_user = User(
        id=uuid.UUID(DEMO_USER_ID),
        email=DEMO_USER_EMAIL,
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhZ8/iGda9iaHeqM1a3huS",  # nosec B106 - Demo password hash
        first_name="Demo",
        last_name="User",
        is_active=True,
        is_mock=True,  # Mark as mock data for easy identification
        created_at=datetime.utcnow(),
    )

    # SECURITY GUARD: Prevent any admin demo account creation
    if DEMO_USER_EMAIL in ["admin@democorp.com", "admin@aiforce.com", "admin@demo.com"]:
        raise ValueError("🚨 SECURITY VIOLATION: Admin demo accounts are prohibited")

    # Check if demo user already exists
    existing_demo = await db.execute(select(User).where(User.id == demo_user.id))
    if not existing_demo.scalar_one_or_none():
        db.add(demo_user)
        print("✓ Created demo user (analyst level - SECURE)")
    else:
        print("✓ Demo user already exists")

    await db.commit()
    return demo_user


async def create_demo_clients(db: AsyncSession):
    """Create demo client accounts."""
    print("Creating demo client accounts...")

    clients = [
        {
            "id": uuid.UUID(DEMO_CLIENT_ID),
            "name": DEMO_CLIENT_NAME,
            "slug": "democorp",
            "description": "Demo corporation for testing platform features",
            "industry": "Technology",
            "company_size": "Enterprise",
            "headquarters_location": "Demo City, Demo State",
            "is_mock": True,  # Mark as mock data
        },
        {
            "id": uuid.UUID("d838573d-f461-44e4-81b5-5af510ef83b7"),
            "name": "Acme Corporation",
            "slug": "acme-corp",
            "description": "Leading technology company specializing in cloud solutions",
            "industry": "Technology",
            "company_size": "Enterprise",
            "headquarters_location": "San Francisco, CA",
            "is_mock": False,
        },
        {
            "id": uuid.UUID("73dee5f1-6a01-43e3-b1b8-dbe6c66f2990"),
            "name": "Marathon Petroleum",
            "slug": "marathon-petroleum",
            "description": "Major energy company with extensive infrastructure",
            "industry": "Energy",
            "company_size": "Enterprise",
            "headquarters_location": "Findlay, OH",
            "is_mock": False,
        },
    ]

    created_clients = []

    for client_data in clients:
        existing = await db.execute(
            select(ClientAccount).where(ClientAccount.id == client_data["id"])
        )
        existing_client = existing.scalar_one_or_none()
        if not existing_client:
            client = ClientAccount(
                id=client_data["id"],
                name=client_data["name"],
                slug=client_data["slug"],
                description=client_data["description"],
                industry=client_data["industry"],
                company_size=client_data["company_size"],
                headquarters_location=client_data["headquarters_location"],
                is_mock=client_data["is_mock"],
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(client)
            created_clients.append(client)
            print(f"✓ Created client: {client_data['name']}")
        else:
            print(f"✓ Client already exists: {client_data['name']}")
            # Use existing client for return
            created_clients.append(existing_client)

    await db.commit()
    return created_clients


async def create_demo_engagements(db: AsyncSession, clients, demo_user):
    """Create demo engagements."""
    print("Creating demo engagements...")

    engagements_data = [
        {
            "id": uuid.UUID(DEMO_ENGAGEMENT_ID),
            "name": DEMO_ENGAGEMENT_NAME,
            "slug": "cloud-migration-2024",
            "description": "Demo engagement for cloud migration project",
            "client_account_id": uuid.UUID(DEMO_CLIENT_ID),
        },
        {
            "id": uuid.UUID("d1a93e23-719d-4dad-8bbf-b66ab9de2b94"),
            "name": "Cloud Migration Initiative 2024",
            "slug": "cloud-migration-initiative-2024",
            "description": "Comprehensive cloud migration project for legacy infrastructure",
            "client_account_id": uuid.UUID("d838573d-f461-44e4-81b5-5af510ef83b7"),
        },
        {
            "id": uuid.UUID("90dd2829-c750-4230-bf70-1728ca370283"),
            "name": "Test Fixed Engagement",
            "slug": "test-fixed-engagement",
            "description": "Fixed engagement for testing purposes",
            "client_account_id": uuid.UUID("d838573d-f461-44e4-81b5-5af510ef83b7"),
        },
        {
            "id": uuid.UUID("baf640df-433c-4bcd-8c8f-7b01c12e9005"),
            "name": "Debug Test Engagement",
            "slug": "debug-test-engagement",
            "description": "Engagement for debugging and testing",
            "client_account_id": uuid.UUID("73dee5f1-6a01-43e3-b1b8-dbe6c66f2990"),
        },
        {
            "id": uuid.UUID("803fbeb6-caaf-4a17-8526-b1a5baccb9bb"),
            "name": "Test Engagement 2",
            "slug": "test-engagement-2",
            "description": "Second test engagement for Marathon Petroleum",
            "client_account_id": uuid.UUID("73dee5f1-6a01-43e3-b1b8-dbe6c66f2990"),
        },
    ]

    created_engagements = []

    for eng_data in engagements_data:
        existing = await db.execute(
            select(Engagement).where(Engagement.id == eng_data["id"])
        )
        existing_engagement = existing.scalar_one_or_none()
        if not existing_engagement:
            engagement = Engagement(
                id=eng_data["id"],
                name=eng_data["name"],
                slug=eng_data["slug"],
                description=eng_data["description"],
                client_account_id=eng_data["client_account_id"],
                engagement_type="migration",
                status="active",
                start_date=datetime.utcnow(),
                created_by=demo_user.id,  # Use demo user as creator
                is_active=True,
                is_mock=eng_data["id"]
                == uuid.UUID(DEMO_ENGAGEMENT_ID),  # Only demo engagement is mock
                created_at=datetime.utcnow(),
            )
            db.add(engagement)
            created_engagements.append(engagement)
            print(f"✓ Created engagement: {eng_data['name']}")
        else:
            print(f"✓ Engagement already exists: {eng_data['name']}")
            created_engagements.append(existing_engagement)

    await db.commit()
    return created_engagements


async def create_demo_sessions(db: AsyncSession, engagements, demo_user):
    """Create demo data import sessions."""
    print("Creating demo data import sessions...")

    sessions_data = [
        {
            "id": uuid.UUID(DEMO_SESSION_ID),
            "session_name": DEMO_SESSION_NAME,
            "client_account_id": uuid.UUID(DEMO_CLIENT_ID),
            "engagement_id": uuid.UUID(DEMO_ENGAGEMENT_ID),
        },
        {
            "id": uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
            "session_name": "Demo Session 1",
            "client_account_id": uuid.UUID("d838573d-f461-44e4-81b5-5af510ef83b7"),
            "engagement_id": uuid.UUID("d1a93e23-719d-4dad-8bbf-b66ab9de2b94"),
        },
        {
            "id": uuid.UUID("b2c3d4e5-f6a7-8901-bcde-f23456789012"),
            "session_name": "Test Session",
            "client_account_id": uuid.UUID("d838573d-f461-44e4-81b5-5af510ef83b7"),
            "engagement_id": uuid.UUID("90dd2829-c750-4230-bf70-1728ca370283"),
        },
    ]

    for session_data in sessions_data:
        existing = await db.execute(
            select(DataImportSession).where(DataImportSession.id == session_data["id"])
        )
        if not existing.scalar_one_or_none():
            session = DataImportSession(
                id=session_data["id"],
                session_name=session_data["session_name"],
                client_account_id=session_data["client_account_id"],
                engagement_id=session_data["engagement_id"],
                created_by=demo_user.id,  # Use demo user as creator
                status="active",
                created_at=datetime.utcnow(),
            )
            db.add(session)
            print(f"✓ Created session: {session_data['session_name']}")
        else:
            print(f"✓ Session already exists: {session_data['session_name']}")

    await db.commit()


async def create_user_profiles(db: AsyncSession, demo_user):
    """Create user profiles for RBAC."""
    print("Creating user profiles...")

    from sqlalchemy import select

    # SECURITY: Only create demo user profile - no admin@democorp profile
    # Demo user profile - Analyst level (SECURE)
    existing_demo_profile = await db.execute(
        select(UserProfile).where(UserProfile.user_id == demo_user.id)
    )
    if not existing_demo_profile.scalar_one_or_none():
        demo_profile = UserProfile(
            user_id=demo_user.id,
            status="active",
            requested_access_level="read_write",  # Analyst level access
            registration_reason="Demo user for testing platform features",
            organization="Democorp",
            role_description="Demo Analyst",
            approved_at=datetime.utcnow(),
            approved_by=demo_user.id,  # Self-approved for demo purposes
            created_at=datetime.utcnow(),
        )
        db.add(demo_profile)
        print("✓ Created demo user profile (Analyst level - SECURE)")
    else:
        print("✓ Demo user profile already exists")

    await db.commit()


async def create_user_roles(db: AsyncSession, demo_user):
    """Create user roles for proper RBAC authorization."""
    print("Creating user roles...")

    import uuid

    from sqlalchemy import select

    from app.models.rbac import RoleType, UserRole

    # SECURITY: Only create demo user role - no admin@democorp role
    # Demo user role (Analyst - SECURE)
    existing_demo_role = await db.execute(
        select(UserRole).where(
            and_(UserRole.user_id == demo_user.id, UserRole.is_active is True)
        )
    )
    if not existing_demo_role.scalar_one_or_none():
        demo_role = UserRole(
            id=uuid.uuid4(),
            user_id=demo_user.id,
            role_type=RoleType.ANALYST,  # SECURITY: Demo user is Analyst, not Admin
            role_name="Demo Analyst",
            description="Demo user with analyst-level access for testing",
            permissions={
                "can_read_data": True,
                "can_write_data": True,
                "can_delete_data": False,
                "can_run_analysis": True,
                "can_view_reports": True,
                "can_export_data": True,
                "can_create_engagements": False,
                "can_modify_configurations": False,
                "can_access_admin_console": False,  # SECURITY: No admin access
            },
            scope_type="global",
            is_active=True,
            assigned_by=demo_user.id,  # Self-assigned for demo purposes
            created_at=datetime.utcnow(),
        )
        db.add(demo_role)
        print("✓ Created demo user role (Analyst - SECURE)")
    else:
        print("✓ Demo user role already exists")

    await db.commit()


async def main():
    """Main function to populate all demo data."""
    print("🚀 Starting demo data population...")
    print("🔒 SECURITY: Only creating demo user account (no admin@democorp)")

    async with AsyncSessionLocal() as db:
        try:
            # Create demo data in order
            demo_user = await create_demo_users(db)
            clients = await create_demo_clients(db)
            engagements = await create_demo_engagements(db, clients, demo_user)
            await create_demo_sessions(db, engagements, demo_user)
            await create_user_profiles(db, demo_user)
            await create_user_roles(db, demo_user)

            print("\n✅ Demo data population completed successfully!")
            print("\n🔒 SECURE Demo credentials:")
            print(f"  Demo User (Analyst): {DEMO_USER_EMAIL} / password")
            print("\n🚫 SECURITY: No admin@democorp account created")

        except Exception as e:
            print(f"\n❌ Error populating demo data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
⚠️ WARNING: DO NOT RUN THIS SCRIPT! ⚠️

This script uses SHA256 password hashing which is incompatible with the 
authentication service that expects bcrypt hashes. Running this script will
set an invalid password hash that will prevent login.

USE INSTEAD: python -m app.core.database_initialization

The database initialization module correctly uses passlib with bcrypt and
will set passwords that work with the authentication service.

---

Setup platform admin account and clean demo data.
Creates a single platform admin for initial platform setup.
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.models import (
    ClientAccount, Engagement, User, UserAccountAssociation,
    DiscoveryFlow, UserRole
)
from app.models.rbac import UserProfile, UserStatus, RoleType


def get_password_hash(password: str) -> str:
    """Simple password hashing for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_demo_uuid() -> uuid.UUID:
    """Create UUID with -def0-def0-def0- pattern in the middle for easy identification (DEFault/DEmo)"""
    import random
    start = ''.join(random.choices('0123456789abcdef', k=8))
    end = ''.join(random.choices('0123456789abcdef', k=12))
    uuid_string = f"{start}-def0-def0-def0-{end}"
    return uuid.UUID(uuid_string)


async def clean_old_demo_data():
    """Clean up old demo data with wrong UUID patterns"""
    print("\n🧹 Cleaning old demo data...")
    async with AsyncSessionLocal() as session:
        # First, clear default_engagement_id from any users to avoid FK constraints
        result = await session.execute(
            select(User).where(User.email.like('%demo%') | User.email.like('%@demo.%'))
        )
        all_demo_users = result.scalars().all()
        for user in all_demo_users:
            user.default_engagement_id = None
            user.default_client_id = None
        await session.commit()
        
        # Delete users with old patterns
        old_pattern_users = [
            "demo@democorp.com",
            "analyst@democorp.com", 
            "viewer@democorp.com",
            "client.admin@democorp.com"
        ]
        
        for email in old_pattern_users:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar()
            if user:
                await session.delete(user)
                print(f"   ❌ Deleted old user: {email}")
        
        # Delete all users with @demo. pattern
        result = await session.execute(
            select(User).where(User.email.like('%@demo.%'))
        )
        demo_domain_users = result.scalars().all()
        for user in demo_domain_users:
            await session.delete(user)
            print(f"   ❌ Deleted demo user: {user.email}")
        
        # Delete old client accounts with 11111111 pattern
        old_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        client = await session.get(ClientAccount, old_client_id)
        if client:
            await session.delete(client)
            print(f"   ❌ Deleted old client: {client.name}")
        
        # Delete any Demo prefixed clients
        result = await session.execute(
            select(ClientAccount).where(ClientAccount.name.like('Demo %'))
        )
        demo_clients = result.scalars().all()
        for client in demo_clients:
            await session.delete(client)
            print(f"   ❌ Deleted demo client: {client.name}")
        
        await session.commit()
        print("✅ Old demo data cleaned")


async def create_platform_admin():
    """Create platform admin account"""
    print("\n👤 Creating platform admin account...")
    async with AsyncSessionLocal() as session:
        # Check if platform admin already exists
        result = await session.execute(
            select(User).where(User.email == "chocka@gmail.com")
        )
        existing_admin = result.scalar()
        
        if existing_admin:
            print("⚠️ Platform admin already exists")
            # Update password if needed
            existing_admin.password_hash = get_password_hash("Password123!")
            await session.commit()
            return existing_admin.id
        
        # Create platform admin user
        admin_id = uuid.uuid4()  # Regular UUID for platform admin
        admin_user = User(
            id=admin_id,
            email="chocka@gmail.com",
            first_name="Platform",
            last_name="Admin",
            password_hash=get_password_hash("Password123!"),
            is_active=True,
            is_verified=True
        )
        session.add(admin_user)
        
        # Create active user profile
        admin_profile = UserProfile(
            user_id=admin_id,
            status=UserStatus.ACTIVE,
            approved_at=datetime.now(timezone.utc),
            registration_reason="Platform Administrator",
            organization="Platform",
            role_description="Platform Administrator with full access",
            requested_access_level="super_admin",
            notification_preferences={"email": True, "slack": False}
        )
        session.add(admin_profile)
        
        # Create platform admin role
        admin_role = UserRole(
            id=uuid.uuid4(),
            user_id=admin_id,
            role_type="platform_admin",
            role_name="Platform Administrator",
            description="Full platform administrative access",
            scope_type="global",
            permissions={
                "can_manage_platform_settings": True,
                "can_manage_all_clients": True,
                "can_manage_all_users": True,
                "can_purge_deleted_data": True,
                "can_view_system_logs": True,
                "can_create_clients": True,
                "can_modify_client_settings": True,
                "can_manage_client_users": True,
                "can_delete_client_data": True,
                "can_create_engagements": True,
                "can_modify_engagement_settings": True,
                "can_manage_engagement_users": True,
                "can_delete_engagement_data": True,
                "can_import_data": True,
                "can_export_data": True,
                "can_view_analytics": True,
                "can_modify_data": True,
                "can_configure_agents": True,
                "can_view_agent_insights": True,
                "can_approve_agent_decisions": True
            },
            is_active=True
        )
        session.add(admin_role)
        
        # Platform admin needs at least one client association to work with the auth system
        # We'll check if there's any client available or create the demo client first
        client_result = await session.execute(
            select(ClientAccount).limit(1)
        )
        any_client = client_result.scalar_one_or_none()
        
        # If no client exists, we'll create one when demo data is created
        # For now, just commit what we have
        await session.commit()
        print(f"✅ Created platform admin: chocka@gmail.com")
        print(f"   ID: {admin_id}")
        print(f"   Password: Password123!")
        
        return admin_id


async def create_minimal_demo_data():
    """Create minimal demo data for testing"""
    print("\n📋 Creating minimal demo data...")
    async with AsyncSessionLocal() as session:
        # Create one demo client with proper demo UUID
        demo_client_id = create_demo_uuid()
        demo_client = ClientAccount(
            id=demo_client_id,
            name="Demo Corporation",
            slug="demo-corp",
            description="Demo client for platform testing",
            industry="Technology",
            company_size="100-500",
            headquarters_location="Demo City, USA",
            primary_contact_name="Demo Contact",
            primary_contact_email="contact@demo-corp.com",
            contact_phone="+1-555-0000"
        )
        session.add(demo_client)
        
        # Create demo engagement
        demo_engagement_id = create_demo_uuid()
        demo_engagement = Engagement(
            id=demo_engagement_id,
            client_account_id=demo_client_id,
            name="Demo Cloud Migration Project",
            slug="demo-cloud-migration",
            description="Demo engagement for testing",
            status="active",
            engagement_type="migration",
            start_date=datetime.now(timezone.utc),
            target_completion_date=datetime(2025, 12, 31, tzinfo=timezone.utc)
        )
        session.add(demo_engagement)
        
        # Commit client and engagement first
        await session.commit()
        
        # Create demo users with different roles
        demo_users = [
            {
                "email": "manager@demo-corp.com",
                "first_name": "Demo",
                "last_name": "Manager",
                "role": RoleType.ENGAGEMENT_MANAGER
            },
            {
                "email": "analyst@demo-corp.com",
                "first_name": "Demo",
                "last_name": "Analyst",
                "role": RoleType.ANALYST
            },
            {
                "email": "viewer@demo-corp.com",
                "first_name": "Demo",
                "last_name": "Viewer",
                "role": RoleType.VIEWER
            }
        ]
        
        for user_data in demo_users:
            user_id = create_demo_uuid()
            
            # Create user
            user = User(
                id=user_id,
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                password_hash=get_password_hash("Demo123!"),
                is_active=True,
                is_verified=True,
                default_client_id=demo_client_id,
                default_engagement_id=demo_engagement_id
            )
            session.add(user)
            
            # Create active profile
            profile = UserProfile(
                user_id=user_id,
                status=UserStatus.ACTIVE,
                approved_at=datetime.now(timezone.utc),
                registration_reason="Demo account",
                organization="Demo Corporation",
                role_description=f"Demo {user_data['role']}",
                requested_access_level="read_write",
                notification_preferences={"email": True, "slack": False}
            )
            session.add(profile)
            
            # Create user role
            user_role = UserRole(
                id=create_demo_uuid(),
                user_id=user_id,
                role_type=user_data["role"].lower(),  # analyst, viewer, etc.
                role_name=user_data["role"].title(),
                description=f"Demo {user_data['role']} role",
                scope_type="engagement",
                scope_client_id=demo_client_id,
                scope_engagement_id=demo_engagement_id,
                permissions={
                    "can_import_data": True,
                    "can_export_data": True,
                    "can_view_analytics": True,
                    "can_manage_users": False,
                    "can_configure_agents": False,
                    "can_access_admin_console": False
                },
                is_active=True
            )
            session.add(user_role)
            
            # Create user-client association
            association = UserAccountAssociation(
                user_id=user_id,
                client_account_id=demo_client_id,
                role=user_data["role"]
            )
            session.add(association)
            
            print(f"   ✅ Created demo user: {user_data['email']} ({user_data['role']})")
        
        await session.commit()
        print("\n✅ Demo data created")
        print(f"   Client: Demo Corporation (ID: {demo_client_id})")
        print(f"   Engagement: Demo Cloud Migration Project")
        print(f"   Demo users password: Demo123!")


async def ensure_platform_admin_association():
    """Ensure platform admin has UserAccountAssociation after demo data is created"""
    print("\n🔗 Ensuring platform admin association...")
    async with AsyncSessionLocal() as session:
        # Get platform admin
        result = await session.execute(
            select(User).where(User.email == "chocka@gmail.com")
        )
        admin = result.scalar()
        
        if not admin:
            print("❌ Platform admin not found!")
            return
            
        # Check if admin has any association
        assoc_result = await session.execute(
            select(UserAccountAssociation).where(
                UserAccountAssociation.user_id == admin.id
            )
        )
        existing_assoc = assoc_result.scalar()
        
        if existing_assoc:
            print("✅ Platform admin already has association")
            return
            
        # Get any client (preferably demo client)
        client_result = await session.execute(
            select(ClientAccount).where(
                ClientAccount.name == "Demo Corporation"
            )
        )
        demo_client = client_result.scalar()
        
        if not demo_client:
            # Get any client
            client_result = await session.execute(
                select(ClientAccount).limit(1)
            )
            demo_client = client_result.scalar()
            
        if demo_client:
            # Create association
            association = UserAccountAssociation(
                id=uuid.uuid4(),
                user_id=admin.id,
                client_account_id=demo_client.id,
                role="platform_admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(association)
            await session.commit()
            print(f"✅ Created platform admin association with client: {demo_client.name}")
        else:
            print("⚠️ No client available for platform admin association")


async def verify_setup():
    """Verify the setup"""
    print("\n🔍 Verifying setup...")
    async with AsyncSessionLocal() as session:
        # Check platform admin
        result = await session.execute(
            select(User).where(User.email == "chocka@gmail.com")
        )
        admin = result.scalar()
        if admin:
            profile = await session.get(UserProfile, admin.id)
            if profile and profile.status == UserStatus.ACTIVE:
                print("✅ Platform admin ready: chocka@gmail.com")
            else:
                print("❌ Platform admin profile not active")
        else:
            print("❌ Platform admin not found")
        
        # Count demo accounts
        result = await session.execute(
            select(ClientAccount).where(ClientAccount.name.like('%Demo%'))
        )
        demo_clients = result.scalars().all()
        print(f"\n📊 Demo clients: {len(demo_clients)}")
        for client in demo_clients:
            print(f"   - {client.name} (ID: {client.id})")


async def main():
    """Main setup process"""
    print("="*60)
    print("🚀 PLATFORM ADMIN SETUP")
    print("="*60)
    
    try:
        # Clean old demo data
        await clean_old_demo_data()
        
        # Create platform admin
        await create_platform_admin()
        
        # Create minimal demo data
        await create_minimal_demo_data()
        
        # Ensure platform admin has association
        await ensure_platform_admin_association()
        
        # Verify
        await verify_setup()
        
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE")
        print("="*60)
        print("\n🔐 Platform Admin Login:")
        print("   Email: chocka@gmail.com")
        print("   Password: Password123!")
        print("\n📝 Platform Admin Capabilities:")
        print("   - Create and manage client accounts")
        print("   - Create client admin users")
        print("   - Full platform access")
        print("\n🎯 Next Steps:")
        print("   1. Login as platform admin")
        print("   2. Create client accounts as needed")
        print("   3. Create client admins who can manage their own engagements")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
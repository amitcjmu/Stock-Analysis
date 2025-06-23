#!/usr/bin/env python3
"""
Script to populate demo data for the AI Force Migration Platform.
This script uses the backend API to create demo data, ensuring consistency with application logic.
"""

import asyncio
import sys
import os
sys.path.append('/app')

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.client_account import User, ClientAccount, Engagement
from app.models.data_import_session import DataImportSession
from app.models.rbac import UserProfile, UserRole, RoleType
from datetime import datetime
import uuid
from sqlalchemy import select, and_

async def create_demo_users(db: AsyncSession):
    """Create demo users."""
    print("Creating demo users...")
    
    # Admin user - using fixed UUID from system design
    admin_user = User(
        id=uuid.UUID('55555555-5555-5555-5555-555555555555'),
        email='admin@democorp.com',
        password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhZ8/iGda9iaHeqM1a3huS',
        first_name='Admin',
        last_name='User',
        is_active=True,
        is_mock=False,
        created_at=datetime.utcnow()
    )
    
    # Demo user - using fixed UUID from system design
    demo_user = User(
        id=uuid.UUID('44444444-4444-4444-4444-444444444444'),
        email='demo@democorp.com',
        password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhZ8/iGda9iaHeqM1a3huS',
        first_name='Demo',
        last_name='User',
        is_active=True,
        is_mock=True,
        created_at=datetime.utcnow()
    )
    
    # Check if users already exist
    existing_admin = await db.execute(select(User).where(User.id == admin_user.id))
    if not existing_admin.scalar_one_or_none():
        db.add(admin_user)
        print("✓ Created admin user")
    else:
        print("✓ Admin user already exists")
    
    existing_demo = await db.execute(select(User).where(User.id == demo_user.id))
    if not existing_demo.scalar_one_or_none():
        db.add(demo_user)
        print("✓ Created demo user")
    else:
        print("✓ Demo user already exists")
    
    await db.commit()
    return admin_user, demo_user

async def create_demo_clients(db: AsyncSession):
    """Create demo client accounts."""
    print("Creating demo client accounts...")
    
    clients = [
        {
            'id': uuid.UUID('11111111-1111-1111-1111-111111111111'),
            'name': 'Democorp',
            'slug': 'democorp',
            'description': 'Demo corporation for testing platform features',
            'industry': 'Technology',
            'company_size': 'Enterprise',
            'headquarters_location': 'Demo City, Demo State',
            'is_mock': True
        },
        {
            'id': uuid.UUID('d838573d-f461-44e4-81b5-5af510ef83b7'),
            'name': 'Acme Corporation',
            'slug': 'acme-corp',
            'description': 'Leading technology company specializing in cloud solutions',
            'industry': 'Technology',
            'company_size': 'Enterprise',
            'headquarters_location': 'San Francisco, CA',
            'is_mock': False
        },
        {
            'id': uuid.UUID('73dee5f1-6a01-43e3-b1b8-dbe6c66f2990'),
            'name': 'Marathon Petroleum',
            'slug': 'marathon-petroleum',
            'description': 'Major energy company with extensive infrastructure',
            'industry': 'Energy',
            'company_size': 'Enterprise',
            'headquarters_location': 'Findlay, OH',
            'is_mock': False
        }
    ]
    
    created_clients = []
    
    for client_data in clients:
        existing = await db.execute(select(ClientAccount).where(ClientAccount.id == client_data['id']))
        existing_client = existing.scalar_one_or_none()
        if not existing_client:
            client = ClientAccount(
                id=client_data['id'],
                name=client_data['name'],
                slug=client_data['slug'],
                description=client_data['description'],
                industry=client_data['industry'],
                company_size=client_data['company_size'],
                headquarters_location=client_data['headquarters_location'],
                is_mock=client_data['is_mock'],
                is_active=True,
                created_at=datetime.utcnow()
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

async def create_demo_engagements(db: AsyncSession, clients, admin_user):
    """Create demo engagements."""
    print("Creating demo engagements...")
    
    engagements_data = [
        {
            'id': uuid.UUID('22222222-2222-2222-2222-222222222222'),
            'name': 'Cloud Migration 2024',
            'slug': 'cloud-migration-2024',
            'description': 'Demo engagement for cloud migration project',
            'client_account_id': uuid.UUID('11111111-1111-1111-1111-111111111111')
        },
        {
            'id': uuid.UUID('d1a93e23-719d-4dad-8bbf-b66ab9de2b94'),
            'name': 'Cloud Migration Initiative 2024',
            'slug': 'cloud-migration-initiative-2024',
            'description': 'Comprehensive cloud migration project for legacy infrastructure',
            'client_account_id': uuid.UUID('d838573d-f461-44e4-81b5-5af510ef83b7')
        },
        {
            'id': uuid.UUID('90dd2829-c750-4230-bf70-1728ca370283'),
            'name': 'Test Fixed Engagement',
            'slug': 'test-fixed-engagement',
            'description': 'Fixed engagement for testing purposes',
            'client_account_id': uuid.UUID('d838573d-f461-44e4-81b5-5af510ef83b7')
        },
        {
            'id': uuid.UUID('baf640df-433c-4bcd-8c8f-7b01c12e9005'),
            'name': 'Debug Test Engagement',
            'slug': 'debug-test-engagement',
            'description': 'Engagement for debugging and testing',
            'client_account_id': uuid.UUID('73dee5f1-6a01-43e3-b1b8-dbe6c66f2990')
        },
        {
            'id': uuid.UUID('803fbeb6-caaf-4a17-8526-b1a5baccb9bb'),
            'name': 'Test Engagement 2',
            'slug': 'test-engagement-2',
            'description': 'Second test engagement for Marathon Petroleum',
            'client_account_id': uuid.UUID('73dee5f1-6a01-43e3-b1b8-dbe6c66f2990')
        }
    ]
    
    created_engagements = []
    
    for eng_data in engagements_data:
        existing = await db.execute(select(Engagement).where(Engagement.id == eng_data['id']))
        existing_engagement = existing.scalar_one_or_none()
        if not existing_engagement:
            engagement = Engagement(
                id=eng_data['id'],
                name=eng_data['name'],
                slug=eng_data['slug'],
                description=eng_data['description'],
                client_account_id=eng_data['client_account_id'],
                engagement_type='migration',
                status='active',
                start_date=datetime.utcnow(),
                created_by=admin_user.id,
                is_active=True,
                is_mock=False,  # Engagements inherit mock status from client
                created_at=datetime.utcnow()
            )
            db.add(engagement)
            created_engagements.append(engagement)
            print(f"✓ Created engagement: {eng_data['name']}")
        else:
            print(f"✓ Engagement already exists: {eng_data['name']}")
            created_engagements.append(existing_engagement)
    
    await db.commit()
    return created_engagements

async def create_demo_sessions(db: AsyncSession, engagements, admin_user):
    """Create demo data import sessions."""
    print("Creating demo data import sessions...")
    
    sessions_data = [
        {
            'id': uuid.UUID('33333333-3333-3333-3333-333333333333'),
            'session_name': 'Demo Session',
            'client_account_id': uuid.UUID('11111111-1111-1111-1111-111111111111'),
            'engagement_id': uuid.UUID('22222222-2222-2222-2222-222222222222')
        },
        {
            'id': uuid.UUID('a1b2c3d4-e5f6-7890-abcd-ef1234567890'),
            'session_name': 'Demo Session 1',
            'client_account_id': uuid.UUID('d838573d-f461-44e4-81b5-5af510ef83b7'),
            'engagement_id': uuid.UUID('d1a93e23-719d-4dad-8bbf-b66ab9de2b94')
        },
        {
            'id': uuid.UUID('b2c3d4e5-f6a7-8901-bcde-f23456789012'),
            'session_name': 'Test Session',
            'client_account_id': uuid.UUID('d838573d-f461-44e4-81b5-5af510ef83b7'),
            'engagement_id': uuid.UUID('90dd2829-c750-4230-bf70-1728ca370283')
        }
    ]
    
    for session_data in sessions_data:
        existing = await db.execute(select(DataImportSession).where(DataImportSession.id == session_data['id']))
        if not existing.scalar_one_or_none():
            session = DataImportSession(
                id=session_data['id'],
                session_name=session_data['session_name'],
                client_account_id=session_data['client_account_id'],
                engagement_id=session_data['engagement_id'],
                created_by=admin_user.id,
                status='active',
                created_at=datetime.utcnow()
            )
            db.add(session)
            print(f"✓ Created session: {session_data['session_name']}")
        else:
            print(f"✓ Session already exists: {session_data['session_name']}")
    
    await db.commit()

async def create_user_profiles(db: AsyncSession, admin_user, demo_user):
    """Create user profiles for RBAC."""
    print("Creating user profiles...")
    
    from sqlalchemy import select
    
    # Admin profile
    existing_admin_profile = await db.execute(select(UserProfile).where(UserProfile.user_id == admin_user.id))
    if not existing_admin_profile.scalar_one_or_none():
        admin_profile = UserProfile(
            user_id=admin_user.id,
            status='active',
            requested_access_level='super_admin',
            registration_reason='Platform administrator',
            organization='AI Force',
            role_description='Platform Administrator',
            approved_at=datetime.utcnow(),
            approved_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        db.add(admin_profile)
        print("✓ Created admin user profile")
    else:
        print("✓ Admin user profile already exists")
    
    # Demo user profile - SECURITY FIX: Demo users should not have admin privileges
    existing_demo_profile = await db.execute(select(UserProfile).where(UserProfile.user_id == demo_user.id))
    if not existing_demo_profile.scalar_one_or_none():
        demo_profile = UserProfile(
            user_id=demo_user.id,
            status='active',
            requested_access_level='read_write',  # CHANGED: was 'admin', now 'read_write' for security
            registration_reason='Demo user for testing',
            organization='Acme Corporation',
            role_description='Demo Analyst',  # CHANGED: was 'Client Administrator', now 'Demo Analyst'
            approved_at=datetime.utcnow(),
            approved_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        db.add(demo_profile)
        print("✓ Created demo user profile (Analyst level - SECURE)")
    else:
        print("✓ Demo user profile already exists")
    
    await db.commit()

async def create_user_roles(db: AsyncSession, admin_user, demo_user):
    """Create user roles for proper RBAC authorization."""
    print("Creating user roles...")
    
    from sqlalchemy import select
    from app.models.rbac import UserRole, RoleType
    import uuid
    
    # Admin user role
    existing_admin_role = await db.execute(select(UserRole).where(
        and_(UserRole.user_id == admin_user.id, UserRole.is_active == True)
    ))
    if not existing_admin_role.scalar_one_or_none():
        admin_role = UserRole(
            id=uuid.uuid4(),
            user_id=admin_user.id,
            role_type=RoleType.PLATFORM_ADMIN,
            role_name='Platform Administrator',
            description='Full platform administrative access',
            permissions={
                "can_read_all_data": True,
                "can_write_all_data": True,
                "can_delete_data": True,
                "can_manage_users": True,
                "can_approve_users": True,
                "can_access_admin_console": True,
                "can_view_audit_logs": True,
                "can_manage_clients": True,
                "can_manage_engagements": True,
                "can_access_llm_usage": True
            },
            scope_type='global',
            is_active=True,
            assigned_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        db.add(admin_role)
        print("✓ Created admin user role")
    else:
        print("✓ Admin user role already exists")
    
    # Demo user role (Analyst - SECURE)
    existing_demo_role = await db.execute(select(UserRole).where(
        and_(UserRole.user_id == demo_user.id, UserRole.is_active == True)
    ))
    if not existing_demo_role.scalar_one_or_none():
        demo_role = UserRole(
            id=uuid.uuid4(),
            user_id=demo_user.id,
            role_type=RoleType.ANALYST,  # SECURITY: Demo user is Analyst, not Admin
            role_name='Demo Analyst',
            description='Demo user with analyst-level access',
            permissions={
                "can_read_data": True,
                "can_write_data": True,
                "can_delete_data": False,
                "can_run_analysis": True,
                "can_view_reports": True,
                "can_export_data": True,
                "can_create_engagements": False,
                "can_modify_configurations": False
            },
            scope_type='global',
            is_active=True,
            assigned_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        db.add(demo_role)
        print("✓ Created demo user role (Analyst - SECURE)")
    else:
        print("✓ Demo user role already exists")
    
    await db.commit()

async def main():
    """Main function to populate all demo data."""
    print("🚀 Starting demo data population...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Create demo data in order
            admin_user, demo_user = await create_demo_users(db)
            clients = await create_demo_clients(db)
            engagements = await create_demo_engagements(db, clients, admin_user)
            await create_demo_sessions(db, engagements, admin_user)
            await create_user_profiles(db, admin_user, demo_user)
            await create_user_roles(db, admin_user, demo_user)
            await create_user_roles(db, admin_user, demo_user)
            
            print("\n✅ Demo data population completed successfully!")
            print("\nDemo credentials:")
            print("  Admin: admin@democorp.com / password")
            print("  Demo:  demo@democorp.com / password")
            
        except Exception as e:
            print(f"\n❌ Error populating demo data: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(main()) 
async def create_user_roles(db: AsyncSession, admin_user, demo_user):
    """Create user roles for proper RBAC authorization."""
    print("Creating user roles...")
    
    from sqlalchemy import select, and_
    from app.models.rbac import UserRole, RoleType
    import uuid
    
    # Admin user role
    existing_admin_role = await db.execute(select(UserRole).where(
        and_(UserRole.user_id == admin_user.id, UserRole.is_active == True)
    ))
    if not existing_admin_role.scalar_one_or_none():
        admin_role = UserRole(
            id=uuid.uuid4(),
            user_id=admin_user.id,
            role_type=RoleType.PLATFORM_ADMIN,
            role_name='Platform Administrator',
            description='Full platform administrative access',
            permissions={
                "can_read_all_data": True,
                "can_write_all_data": True,
                "can_delete_data": True,
                "can_manage_users": True,
                "can_approve_users": True,
                "can_access_admin_console": True,
                "can_view_audit_logs": True,
                "can_manage_clients": True,
                "can_manage_engagements": True,
                "can_access_llm_usage": True
            },
            scope_type='global',
            is_active=True,
            assigned_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        db.add(admin_role)
        print("✓ Created admin user role")
    else:
        print("✓ Admin user role already exists")
    
    # Demo user role (Analyst - SECURE)
    existing_demo_role = await db.execute(select(UserRole).where(
        and_(UserRole.user_id == demo_user.id, UserRole.is_active == True)
    ))
    if not existing_demo_role.scalar_one_or_none():
        demo_role = UserRole(
            id=uuid.uuid4(),
            user_id=demo_user.id,
            role_type=RoleType.ANALYST,  # SECURITY: Demo user is Analyst, not Admin
            role_name='Demo Analyst',
            description='Demo user with analyst-level access',
            permissions={
                "can_read_data": True,
                "can_write_data": True,
                "can_delete_data": False,
                "can_run_analysis": True,
                "can_view_reports": True,
                "can_export_data": True,
                "can_create_engagements": False,
                "can_modify_configurations": False
            },
            scope_type='global',
            is_active=True,
            assigned_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        db.add(demo_role)
        print("✓ Created demo user role (Analyst - SECURE)")
    else:
        print("✓ Demo user role already exists")
    
    await db.commit()

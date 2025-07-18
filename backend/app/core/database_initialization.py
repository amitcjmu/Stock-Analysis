"""
Database Initialization Module
Ensures consistent setup of platform admin, user profiles, and demo data across database changes.

This module is designed to be idempotent and can be run multiple times safely.
It enforces the following requirements:
1. All users MUST have UserProfile records with status='active' to login
2. Platform admin account: chocka@gmail.com / Password123!
3. Demo UUIDs use pattern: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX (DEFault/DEmo pattern)
4. NO demo client admin accounts (only platform admin can create client admins)
5. Demo users are tied to proper client/engagement context

Run this module manually when:
- Setting up a new database
- After major database schema changes
- When demo data needs to be reset
- If users report login issues ("Account not approved")
"""

import asyncio
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, ClientAccount, Engagement
from app.models.rbac import UserProfile, UserStatus, UserRole, RoleType
from app.models.client_account import UserAccountAssociation

# Conditional import to handle migration scenarios
try:
    from app.models.assessment_flow import EngagementArchitectureStandard
    ASSESSMENT_MODELS_AVAILABLE = True
except Exception:
    # Models not available yet (during migration)
    ASSESSMENT_MODELS_AVAILABLE = False
    EngagementArchitectureStandard = None

logger = logging.getLogger(__name__)


class PlatformRequirements:
    """Core platform requirements that must be enforced"""
    
    # Platform admin configuration
    PLATFORM_ADMIN_EMAIL = "chocka@gmail.com"
    PLATFORM_ADMIN_PASSWORD = "Password123!"
    PLATFORM_ADMIN_FIRST_NAME = "Platform"
    PLATFORM_ADMIN_LAST_NAME = "Admin"
    
    # Demo data configuration - Fixed UUIDs for frontend fallback
    DEMO_CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
    DEMO_CLIENT_NAME = "Demo Corporation"
    DEMO_ENGAGEMENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
    DEMO_ENGAGEMENT_NAME = "Demo Cloud Migration Project"
    DEMO_USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
    DEMO_USER_EMAIL = "demo@demo-corp.com"
    DEMO_USER_PASSWORD = "Demo123!"
    
    # Demo users (NO CLIENT ADMINS!)
    DEMO_USERS = [
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
    
    @staticmethod
    def create_demo_uuid() -> uuid.UUID:
        """Create UUID with -def0-def0-def0- pattern for easy identification (DEFault/DEmo)"""
        import random
        start = ''.join(random.choices('0123456789abcdef', k=8))
        end = ''.join(random.choices('0123456789abcdef', k=12))
        uuid_string = f"{start}-def0-def0-def0-{end}"
        return uuid.UUID(uuid_string)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Password hashing using bcrypt to match authentication service"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)


class DatabaseInitializer:
    """Handles database initialization with platform requirements"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.requirements = PlatformRequirements()
    
    async def initialize(self):
        """Run complete initialization process"""
        logger.info("Starting database initialization...")
        
        try:
            # Step 1: Verify assessment flow tables exist
            await self.verify_assessment_tables()
            
            # Step 2: Ensure platform admin exists
            await self.ensure_platform_admin()
            
            # Step 3: Create demo data if needed
            await self.ensure_demo_data()
            
            # Step 4: Initialize assessment standards for existing engagements
            await self.ensure_engagement_assessment_standards()
            
            # Step 5: Verify all users have profiles
            await self.ensure_user_profiles()
            
            # Step 6: Clean up invalid data
            await self.cleanup_invalid_data()
            
            # Step 7: Auto-seed demo data if needed
            await self.auto_seed_demo_data()
            
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def ensure_platform_admin(self):
        """Ensure platform admin account exists with proper configuration"""
        logger.info("Ensuring platform admin exists...")
        
        # Check if platform admin exists
        result = await self.db.execute(
            select(User).where(User.email == self.requirements.PLATFORM_ADMIN_EMAIL)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            # Create platform admin
            admin_id = uuid.uuid4()
            admin = User(
                id=admin_id,
                email=self.requirements.PLATFORM_ADMIN_EMAIL,
                first_name=self.requirements.PLATFORM_ADMIN_FIRST_NAME,
                last_name=self.requirements.PLATFORM_ADMIN_LAST_NAME,
                password_hash=self.requirements.get_password_hash(
                    self.requirements.PLATFORM_ADMIN_PASSWORD
                ),
                is_active=True,
                is_verified=True
            )
            self.db.add(admin)
            await self.db.flush()
            
            logger.info(f"Created platform admin: {admin.email}")
        else:
            # Update password to ensure it's correct
            admin.password_hash = self.requirements.get_password_hash(
                self.requirements.PLATFORM_ADMIN_PASSWORD
            )
            admin.is_active = True
            admin.is_verified = True
            admin_id = admin.id
            
            logger.info(f"Updated platform admin: {admin.email}")
        
        # Ensure platform admin has active profile
        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == admin_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            profile = UserProfile(
                user_id=admin_id,
                status=UserStatus.ACTIVE,
                approved_at=datetime.now(timezone.utc),
                registration_reason="Platform Administrator",
                organization="Platform",
                role_description="Platform Administrator",
                requested_access_level="super_admin"
            )
            self.db.add(profile)
            logger.info("Created platform admin profile")
        else:
            # Ensure profile is active
            profile.status = UserStatus.ACTIVE
            if not profile.approved_at:
                profile.approved_at = datetime.now(timezone.utc)
            logger.info("Updated platform admin profile")
        
        # Ensure platform admin has platform_admin role
        role_result = await self.db.execute(
            select(UserRole).where(
                UserRole.user_id == admin_id,
                UserRole.role_type == "platform_admin"
            )
        )
        role = role_result.scalar_one_or_none()
        
        if not role:
            role = UserRole(
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
            self.db.add(role)
            logger.info("Created platform admin role")
        else:
            role.is_active = True
            logger.info("Updated platform admin role")
        
        # Ensure platform admin has user account association
        # Platform admin needs a global association (can be with a default client for context)
        # First, ensure we have at least one client to associate with
        client_result = await self.db.execute(
            select(ClientAccount).limit(1)
        )
        any_client = client_result.scalar_one_or_none()
        
        if any_client:
            # Check if association exists
            assoc_result = await self.db.execute(
                select(UserAccountAssociation).where(
                    UserAccountAssociation.user_id == admin_id
                )
            )
            association = assoc_result.scalar_one_or_none()
            
            if not association:
                # Create platform admin association
                association = UserAccountAssociation(
                    id=uuid.uuid4(),
                    user_id=admin_id,
                    client_account_id=any_client.id,
                    role="platform_admin",
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(association)
                logger.info(f"Created platform admin association with client: {any_client.name}")
            else:
                # Ensure it's set to platform_admin role
                association.role = "platform_admin"
                association.updated_at = datetime.now(timezone.utc)
                logger.info("Updated platform admin association")
        
        await self.db.commit()
    
    async def ensure_demo_data(self):
        """Create demo client, engagement, and users if they don't exist"""
        logger.info("Ensuring demo data exists...")
        
        # Check for demo client with fixed UUID
        client = await self.db.get(ClientAccount, self.requirements.DEMO_CLIENT_ID)
        
        if not client:
            # Check if a client with the same name or slug exists
            existing = await self.db.execute(
                select(ClientAccount).where(
                    (ClientAccount.name == self.requirements.DEMO_CLIENT_NAME) |
                    (ClientAccount.slug == "demo-corp")
                )
            )
            existing_client = existing.scalar_one_or_none()
            
            if existing_client:
                # Delete the existing client with wrong ID
                logger.info(f"Removing existing demo client with wrong ID: {existing_client.id}")
                # First clear user default references
                await self.db.execute(text("UPDATE users SET default_engagement_id = NULL WHERE default_engagement_id IN (SELECT id FROM engagements WHERE client_account_id = :client_id)"), {"client_id": existing_client.id})
                await self.db.execute(text("UPDATE users SET default_client_id = NULL WHERE default_client_id = :client_id"), {"client_id": existing_client.id})
                # Then delete all references
                await self.db.execute(text("DELETE FROM engagement_access WHERE engagement_id IN (SELECT id FROM engagements WHERE client_account_id = :client_id)"), {"client_id": existing_client.id})
                await self.db.execute(text("DELETE FROM client_access WHERE client_account_id = :client_id"), {"client_id": existing_client.id})
                await self.db.execute(text("DELETE FROM user_roles WHERE scope_engagement_id IN (SELECT id FROM engagements WHERE client_account_id = :client_id)"), {"client_id": existing_client.id})
                await self.db.execute(text("DELETE FROM user_roles WHERE scope_client_id = :client_id"), {"client_id": existing_client.id})
                await self.db.execute(text("DELETE FROM user_account_associations WHERE client_account_id = :client_id"), {"client_id": existing_client.id})
                await self.db.execute(text("DELETE FROM engagements WHERE client_account_id = :client_id"), {"client_id": existing_client.id})
                await self.db.execute(text("DELETE FROM client_accounts WHERE id = :client_id"), {"client_id": existing_client.id})
                await self.db.commit()
            
            # Create demo client with fixed UUID for frontend fallback
            client_id = self.requirements.DEMO_CLIENT_ID
            client = ClientAccount(
                id=client_id,
                name=self.requirements.DEMO_CLIENT_NAME,
                slug="demo-corp",
                description="Demo client for platform testing",
                industry="Technology",
                company_size="100-500",
                headquarters_location="Demo City, USA",
                primary_contact_name="Demo Contact",
                primary_contact_email="contact@demo-corp.com",
                contact_phone="+1-555-0000"
            )
            self.db.add(client)
            await self.db.flush()
            logger.info(f"Created demo client: {client.name}")
        
        # Always use fixed client ID
        client_id = self.requirements.DEMO_CLIENT_ID
        
        # Check for demo engagement with fixed UUID
        engagement = await self.db.get(Engagement, self.requirements.DEMO_ENGAGEMENT_ID)
        
        if not engagement:
            # Create demo engagement with fixed UUID for frontend fallback
            engagement_id = self.requirements.DEMO_ENGAGEMENT_ID
            engagement = Engagement(
                id=engagement_id,
                client_account_id=self.requirements.DEMO_CLIENT_ID,
                name=self.requirements.DEMO_ENGAGEMENT_NAME,
                slug="demo-cloud-migration",
                description="Demo engagement for testing",
                status="active",
                engagement_type="migration",
                start_date=datetime.now(timezone.utc),
                target_completion_date=datetime(2025, 12, 31, tzinfo=timezone.utc)
            )
            self.db.add(engagement)
            await self.db.flush()
            logger.info(f"Created demo engagement: {engagement.name}")
        
        # Always use fixed engagement ID
        engagement_id = self.requirements.DEMO_ENGAGEMENT_ID
        
        await self.db.commit()
        
        # Create primary demo user with fixed UUID
        await self.ensure_primary_demo_user(client_id, engagement_id)
        
        # Create additional demo users with def0-def0-def0 pattern
        for user_data in self.requirements.DEMO_USERS:
            await self.ensure_demo_user(user_data, client_id, engagement_id)
    
    async def ensure_primary_demo_user(
        self,
        client_id: uuid.UUID,
        engagement_id: uuid.UUID
    ):
        """Ensure the primary demo user exists with fixed UUID"""
        # Check if demo user exists
        result = await self.db.execute(
            select(User).where(User.id == self.requirements.DEMO_USER_ID)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create demo user with fixed UUID
            user = User(
                id=self.requirements.DEMO_USER_ID,
                email=self.requirements.DEMO_USER_EMAIL,
                first_name="Demo",
                last_name="User",
                password_hash=self.requirements.get_password_hash(
                    self.requirements.DEMO_USER_PASSWORD
                ),
                is_active=True,
                is_verified=True,
                default_client_id=client_id,
                default_engagement_id=engagement_id
            )
            self.db.add(user)
            await self.db.flush()
            logger.info(f"Created primary demo user: {user.email}")
        else:
            # Update to ensure correct configuration
            user.password_hash = self.requirements.get_password_hash(
                self.requirements.DEMO_USER_PASSWORD
            )
            user.is_active = True
            user.is_verified = True
            user.default_client_id = client_id
            user.default_engagement_id = engagement_id
        
        # Ensure user has active profile
        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == self.requirements.DEMO_USER_ID)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            profile = UserProfile(
                user_id=self.requirements.DEMO_USER_ID,
                status=UserStatus.ACTIVE,
                approved_at=datetime.now(timezone.utc),
                registration_reason="Primary demo account",
                organization=self.requirements.DEMO_CLIENT_NAME,
                role_description="Demo Analyst",
                requested_access_level="read_write"
            )
            self.db.add(profile)
        else:
            profile.status = UserStatus.ACTIVE
            if not profile.approved_at:
                profile.approved_at = datetime.now(timezone.utc)
        
        # Ensure user has analyst role
        role_result = await self.db.execute(
            select(UserRole).where(
                UserRole.user_id == self.requirements.DEMO_USER_ID,
                UserRole.role_type == "analyst"
            )
        )
        role = role_result.scalar_one_or_none()
        
        if not role:
            role = UserRole(
                id=uuid.uuid4(),
                user_id=self.requirements.DEMO_USER_ID,
                role_type="analyst",
                role_name="Analyst",
                description="Primary demo analyst role",
                scope_type="engagement",
                scope_client_id=client_id,
                scope_engagement_id=engagement_id,
                permissions={
                    "can_import_data": True,
                    "can_export_data": True,
                    "can_view_analytics": True,
                    "can_run_analysis": True,
                    "can_manage_users": False,
                    "can_configure_agents": False,
                    "can_access_admin_console": False
                },
                is_active=True
            )
            self.db.add(role)
        else:
            role.is_active = True
        
        # Ensure user account association
        assoc_result = await self.db.execute(
            select(UserAccountAssociation).where(
                UserAccountAssociation.user_id == self.requirements.DEMO_USER_ID,
                UserAccountAssociation.client_account_id == client_id
            )
        )
        association = assoc_result.scalar_one_or_none()
        
        if not association:
            association = UserAccountAssociation(
                id=uuid.uuid4(),
                user_id=self.requirements.DEMO_USER_ID,
                client_account_id=client_id,
                role="analyst",
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(association)
            logger.info(f"Created user association for primary demo user")
        
        # Import RBAC models and create access
        try:
            from app.models.rbac import ClientAccess, EngagementAccess, AccessLevel
            
            # Get platform admin ID
            admin_result = await self.db.execute(
                select(User).where(User.email == self.requirements.PLATFORM_ADMIN_EMAIL)
            )
            platform_admin = admin_result.scalar_one_or_none()
            granted_by_id = platform_admin.id if platform_admin else self.requirements.DEMO_USER_ID
            
            # Ensure ClientAccess
            client_access_result = await self.db.execute(
                select(ClientAccess).where(
                    ClientAccess.user_profile_id == self.requirements.DEMO_USER_ID,
                    ClientAccess.client_account_id == client_id
                )
            )
            client_access = client_access_result.scalar_one_or_none()
            
            if not client_access:
                client_access = ClientAccess(
                    id=uuid.uuid4(),
                    user_profile_id=self.requirements.DEMO_USER_ID,
                    client_account_id=client_id,
                    access_level=AccessLevel.READ_WRITE,
                    permissions={
                        "can_view_data": True,
                        "can_import_data": True,
                        "can_export_data": True,
                        "can_manage_engagements": False,
                        "can_configure_client_settings": False,
                        "can_manage_client_users": False
                    },
                    granted_by=granted_by_id,
                    is_active=True
                )
                self.db.add(client_access)
                logger.info(f"Created ClientAccess for primary demo user")
            
            # Ensure EngagementAccess
            engagement_access_result = await self.db.execute(
                select(EngagementAccess).where(
                    EngagementAccess.user_profile_id == self.requirements.DEMO_USER_ID,
                    EngagementAccess.engagement_id == engagement_id
                )
            )
            engagement_access = engagement_access_result.scalar_one_or_none()
            
            if not engagement_access:
                engagement_access = EngagementAccess(
                    id=uuid.uuid4(),
                    user_profile_id=self.requirements.DEMO_USER_ID,
                    engagement_id=engagement_id,
                    access_level=AccessLevel.READ_WRITE,
                    engagement_role="Analyst",
                    permissions={
                        "can_view_data": True,
                        "can_import_data": True,
                        "can_export_data": True,
                        "can_manage_sessions": False,
                        "can_configure_agents": False,
                        "can_approve_migration_decisions": False
                    },
                    granted_by=granted_by_id,
                    is_active=True
                )
                self.db.add(engagement_access)
                logger.info(f"Created EngagementAccess for primary demo user")
                
        except ImportError as e:
            logger.warning(f"RBAC models not available during initialization: {e}")
        
        await self.db.commit()
        logger.info("Primary demo user setup complete")
    
    async def ensure_demo_user(
        self, 
        user_data: Dict, 
        client_id: uuid.UUID, 
        engagement_id: uuid.UUID
    ):
        """Ensure a demo user exists with proper configuration"""
        # Check if user exists
        result = await self.db.execute(
            select(User).where(User.email == user_data["email"])
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create user
            user_id = self.requirements.create_demo_uuid()
            user = User(
                id=user_id,
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                password_hash=self.requirements.get_password_hash(
                    self.requirements.DEMO_USER_PASSWORD
                ),
                is_active=True,
                is_verified=True,
                default_client_id=client_id,
                default_engagement_id=engagement_id
            )
            self.db.add(user)
            await self.db.flush()
            logger.info(f"Created demo user: {user.email}")
        else:
            # Update user to ensure correct configuration
            user.password_hash = self.requirements.get_password_hash(
                self.requirements.DEMO_USER_PASSWORD
            )
            user.is_active = True
            user.is_verified = True
            user.default_client_id = client_id
            user.default_engagement_id = engagement_id
            user_id = user.id
        
        # Ensure user has active profile
        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            profile = UserProfile(
                user_id=user_id,
                status=UserStatus.ACTIVE,
                approved_at=datetime.now(timezone.utc),
                registration_reason="Demo account",
                organization=self.requirements.DEMO_CLIENT_NAME,
                role_description=f"Demo {user_data['role'].value}",
                requested_access_level="read_write"
            )
            self.db.add(profile)
        else:
            profile.status = UserStatus.ACTIVE
            if not profile.approved_at:
                profile.approved_at = datetime.now(timezone.utc)
        
        # Ensure user has proper role
        role_result = await self.db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_type == user_data["role"].value.lower()
            )
        )
        role = role_result.scalar_one_or_none()
        
        if not role:
            role = UserRole(
                id=self.requirements.create_demo_uuid(),
                user_id=user_id,
                role_type=user_data["role"].value.lower(),
                role_name=user_data["role"].value.title(),
                description=f"Demo {user_data['role'].value} role",
                scope_type="engagement",
                scope_client_id=client_id,
                scope_engagement_id=engagement_id,
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
            self.db.add(role)
        else:
            role.is_active = True
        
        # Ensure user has account association
        assoc_result = await self.db.execute(
            select(UserAccountAssociation).where(
                UserAccountAssociation.user_id == user_id,
                UserAccountAssociation.client_account_id == client_id
            )
        )
        association = assoc_result.scalar_one_or_none()
        
        if not association:
            # Create user account association
            association = UserAccountAssociation(
                id=self.requirements.create_demo_uuid(),
                user_id=user_id,
                client_account_id=client_id,
                role=user_data["role"].value.lower(),
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(association)
            logger.info(f"Created user association for {user.email} with role {user_data['role'].value}")
        else:
            # Update role if needed
            association.role = user_data["role"].value.lower()
            association.updated_at = datetime.now(timezone.utc)
        
        # Import RBAC models conditionally to avoid circular imports
        try:
            from app.models.rbac import ClientAccess, EngagementAccess, AccessLevel
            
            # Get platform admin ID to use as granted_by
            admin_result = await self.db.execute(
                select(User).where(User.email == self.requirements.PLATFORM_ADMIN_EMAIL)
            )
            platform_admin = admin_result.scalar_one_or_none()
            granted_by_id = platform_admin.id if platform_admin else user_id  # Use self if no admin found
            
            # Ensure user has ClientAccess for RBAC
            client_access_result = await self.db.execute(
                select(ClientAccess).where(
                    ClientAccess.user_profile_id == user_id,
                    ClientAccess.client_account_id == client_id
                )
            )
            client_access = client_access_result.scalar_one_or_none()
            
            if not client_access:
                # Determine access level based on role
                access_level_map = {
                    'viewer': AccessLevel.READ_ONLY,
                    'analyst': AccessLevel.READ_WRITE,
                    'engagement_manager': AccessLevel.ADMIN
                }
                access_level = access_level_map.get(user_data["role"].value.lower(), AccessLevel.READ_ONLY)
                
                client_access = ClientAccess(
                    id=self.requirements.create_demo_uuid(),
                    user_profile_id=user_id,
                    client_account_id=client_id,
                    access_level=access_level,
                    permissions={
                        "can_view_data": True,
                        "can_import_data": access_level in [AccessLevel.READ_WRITE, AccessLevel.ADMIN],
                        "can_export_data": True,
                        "can_manage_engagements": access_level == AccessLevel.ADMIN,
                        "can_configure_client_settings": access_level == AccessLevel.ADMIN,
                        "can_manage_client_users": access_level == AccessLevel.ADMIN
                    },
                    granted_by=granted_by_id,  # Platform admin or self
                    is_active=True
                )
                self.db.add(client_access)
                logger.info(f"Created ClientAccess for {user.email} with {access_level} access")
            
            # Ensure user has EngagementAccess for RBAC
            engagement_access_result = await self.db.execute(
                select(EngagementAccess).where(
                    EngagementAccess.user_profile_id == user_id,
                    EngagementAccess.engagement_id == engagement_id
                )
            )
            engagement_access = engagement_access_result.scalar_one_or_none()
            
            if not engagement_access:
                access_level = access_level_map.get(user_data["role"].value.lower(), AccessLevel.READ_ONLY)
                
                engagement_access = EngagementAccess(
                    id=self.requirements.create_demo_uuid(),
                    user_profile_id=user_id,
                    engagement_id=engagement_id,
                    access_level=access_level,
                    engagement_role=user_data["role"].value.title(),
                    permissions={
                        "can_view_data": True,
                        "can_import_data": access_level in [AccessLevel.READ_WRITE, AccessLevel.ADMIN],
                        "can_export_data": True,
                        "can_manage_sessions": access_level == AccessLevel.ADMIN,
                        "can_configure_agents": access_level == AccessLevel.ADMIN,
                        "can_approve_migration_decisions": access_level == AccessLevel.ADMIN
                    },
                    granted_by=granted_by_id,  # Platform admin or self
                    is_active=True
                )
                self.db.add(engagement_access)
                logger.info(f"Created EngagementAccess for {user.email} to engagement {engagement_id}")
                
        except ImportError as e:
            logger.warning(f"RBAC models not available during initialization: {e}")
        
        await self.db.commit()
    
    async def ensure_user_profiles(self):
        """Ensure all users have active profiles (required for login)"""
        logger.info("Ensuring all users have profiles...")
        
        # Find users without profiles
        from sqlalchemy import text
        
        query = text("""
        SELECT u.id, u.email, u.first_name, u.last_name
        FROM users u
        LEFT JOIN user_profiles up ON u.id = up.user_id
        WHERE up.user_id IS NULL
        """)
        
        result = await self.db.execute(query)
        users_without_profiles = result.fetchall()
        
        for user_id, email, first_name, last_name in users_without_profiles:
            profile = UserProfile(
                user_id=user_id,
                status=UserStatus.ACTIVE,
                approved_at=datetime.now(timezone.utc),
                registration_reason="Auto-created profile",
                organization="Unknown",
                role_description="User",
                requested_access_level="read_only"
            )
            self.db.add(profile)
            logger.warning(f"Created missing profile for user: {email}")
        
        if users_without_profiles:
            await self.db.commit()
    
    async def cleanup_invalid_data(self):
        """Clean up any invalid demo data"""
        logger.info("Cleaning up invalid data...")
        
        # Remove any demo client admins (they should not exist)
        result = await self.db.execute(
            select(UserRole).where(
                UserRole.role_type == RoleType.CLIENT_ADMIN.value,
                UserRole.user_id.in_(
                    select(User.id).where(User.email.like("%demo%"))
                )
            )
        )
        invalid_roles = result.scalars().all()
        
        for role in invalid_roles:
            await self.db.delete(role)
            logger.warning(f"Removed invalid demo client admin role: {role.id}")
        
        if invalid_roles:
            await self.db.commit()
    
    async def verify_assessment_tables(self):
        """Verify assessment flow tables exist and are properly configured"""
        logger.info("Verifying assessment flow tables...")
        
        required_tables = [
            'assessment_flows',
            'engagement_architecture_standards', 
            'application_architecture_overrides',
            'application_components',
            'tech_debt_analysis',
            'component_treatments',
            'sixr_decisions',
            'assessment_learning_feedback'
        ]
        
        missing_tables = []
        for table in required_tables:
            try:
                result = await self.db.execute(
                    text("SELECT to_regclass(:table_name)"), 
                    {"table_name": table}
                )
                if not result.scalar():
                    missing_tables.append(table)
            except Exception as e:
                logger.warning(f"Could not verify table {table}: {e}")
                missing_tables.append(table)
        
        if missing_tables:
            raise Exception(f"Missing assessment flow tables: {', '.join(missing_tables)}. Please run migration 002_add_assessment_flow_tables.")
        
        logger.info("Assessment flow tables verified successfully")
    
    async def ensure_engagement_assessment_standards(self):
        """Initialize assessment standards for existing engagements"""
        logger.info("Ensuring assessment standards for all engagements...")
        
        try:
            # Import here to avoid circular imports
            if ASSESSMENT_MODELS_AVAILABLE:
                from app.core.seed_data.assessment_standards import initialize_assessment_standards
            
            # Get all active engagements
            result = await self.db.execute(
                select(Engagement).where(Engagement.status == 'active')
            )
            engagements = result.scalars().all()
            
            standards_initialized = 0
            if ASSESSMENT_MODELS_AVAILABLE and EngagementArchitectureStandard:
                for engagement in engagements:
                    # Check if standards already exist
                    existing_standards = await self.db.execute(
                        select(EngagementArchitectureStandard)
                        .where(EngagementArchitectureStandard.engagement_id == engagement.id)
                    )
                    
                    if not existing_standards.first():
                        try:
                            await initialize_assessment_standards(self.db, str(engagement.id))
                            standards_initialized += 1
                            logger.info(f"Initialized assessment standards for engagement: {engagement.name}")
                        except Exception as e:
                            logger.error(f"Failed to initialize standards for engagement {engagement.id}: {str(e)}")
                            continue
                    else:
                        logger.debug(f"Standards already exist for engagement: {engagement.name}")
            else:
                logger.info("Assessment models not available yet, skipping standards initialization")
            
            if standards_initialized > 0:
                logger.info(f"Successfully initialized assessment standards for {standards_initialized} engagements")
            else:
                logger.info("All engagements already have assessment standards")
                
        except Exception as e:
            logger.error(f"Failed to ensure engagement assessment standards: {str(e)}")
            # Don't raise here - this shouldn't block the main initialization
    
    async def auto_seed_demo_data(self):
        """Auto-seed comprehensive demo data if needed"""
        logger.info("Checking if demo data seeding is needed...")
        
        try:
            # Import the auto seeder
            from app.core.auto_seed_demo_data import auto_seed_demo_data
            
            # Run auto-seeding
            seeded = await auto_seed_demo_data(self.db)
            
            if seeded:
                logger.info("✅ Demo data seeded successfully!")
            else:
                logger.info("Demo data already exists or seeding was skipped")
                
        except ImportError as e:
            logger.warning(f"Auto-seeder not available: {e}")
        except Exception as e:
            logger.error(f"Failed to auto-seed demo data: {e}")
            # Don't raise - this shouldn't block initialization


async def initialize_database(db: AsyncSession):
    """Main entry point for database initialization"""
    initializer = DatabaseInitializer(db)
    await initializer.initialize()


# Make this available as a CLI command
if __name__ == "__main__":
    import asyncio
    from app.core.database import AsyncSessionLocal
    
    async def main():
        async with AsyncSessionLocal() as db:
            await initialize_database(db)
            print("✅ Database initialization completed!")
    
    asyncio.run(main())
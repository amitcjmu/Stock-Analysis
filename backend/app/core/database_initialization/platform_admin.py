"""
Platform administrator setup and management.

This module handles the creation and maintenance of the platform administrator
account with proper roles, permissions, and profile configuration.
"""

import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, ClientAccount
from app.models.client_account import UserAccountAssociation
from app.models.rbac import UserProfile, UserRole, UserStatus
from .base import PlatformRequirements

logger = logging.getLogger(__name__)


class PlatformAdminManager:
    """Manages platform administrator account setup"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.requirements = PlatformRequirements()

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
                is_verified=True,
                is_admin=True,
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
            admin.is_admin = True
            admin_id = admin.id

            logger.info(f"Updated platform admin: {admin.email}")

        # Ensure platform admin has active profile
        await self._ensure_admin_profile(admin_id)

        # Ensure platform admin has platform_admin role
        await self._ensure_admin_role(admin_id)

        # Ensure platform admin has user account association
        await self._ensure_admin_association(admin_id)

        await self.db.commit()

    async def _ensure_admin_profile(self, admin_id: uuid.UUID):
        """Ensure platform admin has an active profile"""
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
                requested_access_level="super_admin",
            )
            self.db.add(profile)
            logger.info("Created platform admin profile")
        else:
            # Ensure profile is active
            profile.status = UserStatus.ACTIVE
            if not profile.approved_at:
                profile.approved_at = datetime.now(timezone.utc)
            logger.info("Updated platform admin profile")

    async def _ensure_admin_role(self, admin_id: uuid.UUID):
        """Ensure platform admin has the proper role with full permissions"""
        role_result = await self.db.execute(
            select(UserRole).where(
                UserRole.user_id == admin_id, UserRole.role_type == "platform_admin"
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
                permissions=self._get_platform_admin_permissions(),
                is_active=True,
            )
            self.db.add(role)
            logger.info("Created platform admin role")
        else:
            role.is_active = True
            logger.info("Updated platform admin role")

    def _get_platform_admin_permissions(self) -> dict:
        """Get full permission set for platform admin"""
        return {
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
            "can_approve_agent_decisions": True,
        }

    async def _ensure_admin_association(self, admin_id: uuid.UUID):
        """Ensure platform admin has user account association"""
        # Platform admin needs a global association (can be with a default client for context)
        # First, ensure we have at least one client to associate with
        client_result = await self.db.execute(select(ClientAccount).limit(1))
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
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(association)
                logger.info(
                    f"Created platform admin association with client: {any_client.name}"
                )
            else:
                # Ensure it's set to platform_admin role
                association.role = "platform_admin"
                association.updated_at = datetime.now(timezone.utc)
                logger.info("Updated platform admin association")

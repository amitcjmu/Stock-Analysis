"""
Demo user creation and management.

This module handles creation of demo users with proper profiles and roles.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.client_account import UserAccountAssociation
from app.models.rbac import UserProfile, UserRole, UserStatus
from ..base import PlatformRequirements

logger = logging.getLogger(__name__)


class DemoUserSetup:
    """Manages demo user creation and configuration"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.requirements = PlatformRequirements()

    async def ensure_primary_demo_user(
        self, client_id: uuid.UUID, engagement_id: uuid.UUID
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
                default_engagement_id=engagement_id,
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
        await self._ensure_user_profile(
            self.requirements.DEMO_USER_ID, "Primary demo account"
        )

        # Ensure user has analyst role
        await self._ensure_user_role(
            self.requirements.DEMO_USER_ID, "analyst", client_id, engagement_id
        )

        # Ensure user account association
        await self._ensure_user_association(
            self.requirements.DEMO_USER_ID, client_id, "analyst"
        )

        await self.db.commit()
        logger.info("Primary demo user setup complete")

    async def ensure_demo_user(
        self, user_data: Dict, client_id: uuid.UUID, engagement_id: uuid.UUID
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
                default_engagement_id=engagement_id,
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
        await self._ensure_user_profile(
            user_id, "Demo account", user_data["role"].value
        )

        # Ensure user has proper role
        await self._ensure_user_role(
            user_id, user_data["role"].value.lower(), client_id, engagement_id
        )

        # Ensure user has account association
        await self._ensure_user_association(
            user_id, client_id, user_data["role"].value.lower()
        )

        await self.db.commit()

    async def _ensure_user_profile(
        self, user_id: uuid.UUID, registration_reason: str, role_desc: str = None
    ):
        """Ensure user has an active profile"""
        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(
                user_id=user_id,
                status=UserStatus.ACTIVE,
                approved_at=datetime.now(timezone.utc),
                registration_reason=registration_reason,
                organization=self.requirements.DEMO_CLIENT_NAME,
                role_description=role_desc or "Demo Analyst",
                requested_access_level="read_write",
            )
            self.db.add(profile)
        else:
            profile.status = UserStatus.ACTIVE
            if not profile.approved_at:
                profile.approved_at = datetime.now(timezone.utc)

    async def _ensure_user_role(
        self,
        user_id: uuid.UUID,
        role_type: str,
        client_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ):
        """Ensure user has the specified role"""
        role_result = await self.db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_type == role_type,
            )
        )
        role = role_result.scalar_one_or_none()

        if not role:
            permissions = self._get_role_permissions(role_type)
            role = UserRole(
                id=self.requirements.create_demo_uuid(),
                user_id=user_id,
                role_type=role_type,
                role_name=role_type.title(),
                description=f"Demo {role_type} role",
                scope_type="engagement",
                scope_client_id=client_id,
                scope_engagement_id=engagement_id,
                permissions=permissions,
                is_active=True,
            )
            self.db.add(role)
        else:
            role.is_active = True

    async def _ensure_user_association(
        self, user_id: uuid.UUID, client_id: uuid.UUID, role: str
    ):
        """Ensure user has account association"""
        assoc_result = await self.db.execute(
            select(UserAccountAssociation).where(
                UserAccountAssociation.user_id == user_id,
                UserAccountAssociation.client_account_id == client_id,
            )
        )
        association = assoc_result.scalar_one_or_none()

        if not association:
            association = UserAccountAssociation(
                id=self.requirements.create_demo_uuid(),
                user_id=user_id,
                client_account_id=client_id,
                role=role,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(association)
        else:
            association.role = role
            association.updated_at = datetime.now(timezone.utc)

    def _get_role_permissions(self, role_type: str) -> dict:
        """Get permissions based on role type"""
        base_permissions = {
            "can_import_data": True,
            "can_export_data": True,
            "can_view_analytics": True,
            "can_manage_users": False,
            "can_configure_agents": False,
            "can_access_admin_console": False,
        }

        if role_type == "engagement_manager":
            base_permissions.update(
                {
                    "can_run_analysis": True,
                    "can_approve_migration_decisions": True,
                }
            )

        return base_permissions

    async def get_demo_users_summary(self) -> dict:
        """Get summary of all demo users"""
        # Get primary demo user
        primary_user = await self.db.get(User, self.requirements.DEMO_USER_ID)

        # Get all demo users (those with def0-def0-def0 pattern or fixed demo emails)
        demo_emails = [user["email"] for user in self.requirements.DEMO_USERS]
        demo_emails.append(self.requirements.DEMO_USER_EMAIL)

        result = await self.db.execute(select(User).where(User.email.in_(demo_emails)))
        all_demo_users = result.scalars().all()

        return {
            "primary_user": {
                "email": primary_user.email if primary_user else None,
                "id": str(primary_user.id) if primary_user else None,
                "active": primary_user.is_active if primary_user else False,
            },
            "total_demo_users": len(all_demo_users),
            "demo_user_emails": [user.email for user in all_demo_users],
            "configured_roles": len(self.requirements.DEMO_USERS),
        }

"""
Demo RBAC (Role-Based Access Control) setup.

This module handles creation of RBAC access records for demo users.
"""

import uuid
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from ..base import PlatformRequirements

logger = logging.getLogger(__name__)


class DemoRBACSetup:
    """Manages RBAC access records for demo users"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.requirements = PlatformRequirements()

    async def ensure_rbac_access(
        self,
        user_id: uuid.UUID,
        client_id: uuid.UUID,
        engagement_id: uuid.UUID,
        role: str,
    ):
        """Ensure user has RBAC access records"""
        try:
            from app.models.rbac import AccessLevel

            # Get platform admin ID to use as granted_by
            admin_result = await self.db.execute(
                select(User).where(User.email == self.requirements.PLATFORM_ADMIN_EMAIL)
            )
            platform_admin = admin_result.scalar_one_or_none()
            granted_by_id = platform_admin.id if platform_admin else user_id

            # Determine access level based on role
            access_level_map = {
                "viewer": AccessLevel.READ_ONLY,
                "analyst": AccessLevel.READ_WRITE,
                "engagement_manager": AccessLevel.ADMIN,
            }
            access_level = access_level_map.get(role, AccessLevel.READ_ONLY)

            # Ensure ClientAccess
            await self._ensure_client_access(
                user_id, client_id, access_level, granted_by_id
            )

            # Ensure EngagementAccess
            await self._ensure_engagement_access(
                user_id, engagement_id, access_level, granted_by_id, role
            )

        except ImportError as e:
            logger.warning(f"RBAC models not available during initialization: {e}")

    async def _ensure_client_access(
        self,
        user_id: uuid.UUID,
        client_id: uuid.UUID,
        access_level,
        granted_by_id: uuid.UUID,
    ):
        """Ensure user has ClientAccess record"""
        from app.models.rbac import ClientAccess, AccessLevel

        client_access_result = await self.db.execute(
            select(ClientAccess).where(
                ClientAccess.user_profile_id == user_id,
                ClientAccess.client_account_id == client_id,
            )
        )
        client_access = client_access_result.scalar_one_or_none()

        if not client_access:
            client_access = ClientAccess(
                id=self.requirements.create_demo_uuid(),
                user_profile_id=user_id,
                client_account_id=client_id,
                access_level=access_level,
                permissions={
                    "can_view_data": True,
                    "can_import_data": access_level
                    in [AccessLevel.READ_WRITE, AccessLevel.ADMIN],
                    "can_export_data": True,
                    "can_manage_engagements": access_level == AccessLevel.ADMIN,
                    "can_configure_client_settings": access_level == AccessLevel.ADMIN,
                    "can_manage_client_users": access_level == AccessLevel.ADMIN,
                },
                granted_by=granted_by_id,
                is_active=True,
            )
            self.db.add(client_access)
            logger.info(
                f"Created ClientAccess for user {user_id} with {access_level} access"
            )

    async def _ensure_engagement_access(
        self,
        user_id: uuid.UUID,
        engagement_id: uuid.UUID,
        access_level,
        granted_by_id: uuid.UUID,
        role: str,
    ):
        """Ensure user has EngagementAccess record"""
        from app.models.rbac import EngagementAccess, AccessLevel

        engagement_access_result = await self.db.execute(
            select(EngagementAccess).where(
                EngagementAccess.user_profile_id == user_id,
                EngagementAccess.engagement_id == engagement_id,
            )
        )
        engagement_access = engagement_access_result.scalar_one_or_none()

        if not engagement_access:
            engagement_access = EngagementAccess(
                id=self.requirements.create_demo_uuid(),
                user_profile_id=user_id,
                engagement_id=engagement_id,
                access_level=access_level,
                engagement_role=role.title(),
                permissions={
                    "can_view_data": True,
                    "can_import_data": access_level
                    in [AccessLevel.READ_WRITE, AccessLevel.ADMIN],
                    "can_export_data": True,
                    "can_manage_sessions": access_level == AccessLevel.ADMIN,
                    "can_configure_agents": access_level == AccessLevel.ADMIN,
                    "can_approve_migration_decisions": access_level
                    == AccessLevel.ADMIN,
                },
                granted_by=granted_by_id,
                is_active=True,
            )
            self.db.add(engagement_access)
            logger.info(
                f"Created EngagementAccess for user {user_id} to engagement {engagement_id}"
            )

    async def audit_rbac_permissions(self, user_id: uuid.UUID) -> dict:
        """Audit RBAC permissions for a user"""
        audit_result = {
            "user_id": str(user_id),
            "client_access": None,
            "engagement_access": None,
            "issues": [],
        }

        try:
            from app.models.rbac import ClientAccess, EngagementAccess

            # Check ClientAccess
            client_access_result = await self.db.execute(
                select(ClientAccess).where(ClientAccess.user_profile_id == user_id)
            )
            client_access = client_access_result.scalar_one_or_none()

            if client_access:
                audit_result["client_access"] = {
                    "exists": True,
                    "access_level": client_access.access_level.value,
                    "is_active": client_access.is_active,
                    "permissions_count": (
                        len(client_access.permissions)
                        if client_access.permissions
                        else 0
                    ),
                }
            else:
                audit_result["client_access"] = {"exists": False}
                audit_result["issues"].append("Missing ClientAccess record")

            # Check EngagementAccess
            engagement_access_result = await self.db.execute(
                select(EngagementAccess).where(
                    EngagementAccess.user_profile_id == user_id
                )
            )
            engagement_access = engagement_access_result.scalar_one_or_none()

            if engagement_access:
                audit_result["engagement_access"] = {
                    "exists": True,
                    "access_level": engagement_access.access_level.value,
                    "engagement_role": engagement_access.engagement_role,
                    "is_active": engagement_access.is_active,
                    "permissions_count": (
                        len(engagement_access.permissions)
                        if engagement_access.permissions
                        else 0
                    ),
                }
            else:
                audit_result["engagement_access"] = {"exists": False}
                audit_result["issues"].append("Missing EngagementAccess record")

        except ImportError:
            audit_result["issues"].append("RBAC models not available")

        return audit_result

    async def cleanup_orphaned_rbac_records(self):
        """Clean up orphaned RBAC records"""
        try:
            from sqlalchemy import text

            logger.info("Cleaning up orphaned RBAC records...")

            # Clean up ClientAccess records for non-existent users
            result = await self.db.execute(
                text(
                    """
                DELETE FROM client_access
                WHERE user_profile_id NOT IN (SELECT id FROM users)
                """
                )
            )
            deleted_client_access = result.rowcount

            # Clean up EngagementAccess records for non-existent users
            result = await self.db.execute(
                text(
                    """
                DELETE FROM engagement_access
                WHERE user_profile_id NOT IN (SELECT id FROM users)
                """
                )
            )
            deleted_engagement_access = result.rowcount

            if deleted_client_access > 0 or deleted_engagement_access > 0:
                await self.db.commit()
                logger.info(
                    f"Cleaned up {deleted_client_access} orphaned ClientAccess and "
                    f"{deleted_engagement_access} orphaned EngagementAccess records"
                )
            else:
                logger.info("No orphaned RBAC records found")

        except ImportError:
            logger.info("RBAC models not available, skipping cleanup")
        except Exception as e:
            logger.error(f"Error cleaning up RBAC records: {e}")
            await self.db.rollback()

"""
Base handler for RBAC operations with common functionality.
"""

import logging
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

# Import RBAC models with fallback
try:
    from app.models.rbac import (AccessAuditLog, AccessLevel, ClientAccess,
                                 EngagementAccess, RoleType, UserProfile,
                                 UserRole, UserStatus)

    RBAC_MODELS_AVAILABLE = True
except ImportError:
    RBAC_MODELS_AVAILABLE = False
    UserProfile = UserRole = ClientAccess = EngagementAccess = AccessAuditLog = None
    UserStatus = AccessLevel = RoleType = None

# Import user and client models with fallback
try:
    from app.models.client_account import ClientAccount, Engagement, User

    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    ClientAccount = Engagement = User = None

logger = logging.getLogger(__name__)


class BaseRBACHandler:
    """Base handler with common RBAC functionality."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.is_available = RBAC_MODELS_AVAILABLE and CLIENT_MODELS_AVAILABLE

        if not self.is_available:
            logger.warning(
                "RBAC Handler initialized with limited functionality due to missing models"
            )

    def _get_default_permissions(self, access_level: str) -> Dict[str, bool]:
        """Get default permissions based on access level."""
        if access_level == AccessLevel.READ_ONLY:
            return {
                "view_assets": True,
                "view_reports": True,
                "export_data": True,
                "view_migration_plans": True,
                "view_engagement_overview": True,
                "upload_data": False,
                "modify_settings": False,
                "approve_migrations": False,
                "manage_users": False,
                "create_engagements": False,
                "delete_data": False,
            }

        elif access_level == AccessLevel.READ_WRITE or access_level == "analyst":
            return {
                "view_assets": True,
                "view_reports": True,
                "export_data": True,
                "view_migration_plans": True,
                "view_engagement_overview": True,
                "upload_data": True,
                "modify_settings": True,
                "create_analysis": True,
                "modify_classification": True,
                "generate_reports": True,
                "approve_migrations": False,
                "manage_users": False,
                "create_engagements": False,
                "delete_data": False,
            }

        elif access_level == AccessLevel.ADMIN or access_level == "manager":
            return {
                "view_assets": True,
                "view_reports": True,
                "export_data": True,
                "view_migration_plans": True,
                "view_engagement_overview": True,
                "upload_data": True,
                "modify_settings": True,
                "create_analysis": True,
                "modify_classification": True,
                "generate_reports": True,
                "approve_migrations": True,
                "manage_team_users": True,
                "create_engagements": True,
                "manage_engagement_settings": True,
                "approve_budgets": True,
                "manage_users": False,
                "delete_data": False,
            }

        elif access_level == AccessLevel.SUPER_ADMIN:
            return {
                "view_assets": True,
                "view_reports": True,
                "export_data": True,
                "view_migration_plans": True,
                "view_engagement_overview": True,
                "upload_data": True,
                "modify_settings": True,
                "create_analysis": True,
                "modify_classification": True,
                "generate_reports": True,
                "approve_migrations": True,
                "manage_users": True,
                "create_engagements": True,
                "manage_engagement_settings": True,
                "approve_budgets": True,
                "delete_data": True,
                "system_administration": True,
                "platform_configuration": True,
            }

        else:
            # Default to read-only
            return self._get_default_permissions(AccessLevel.READ_ONLY)

    def _get_default_role_permissions(self, access_level: str) -> Dict[str, bool]:
        """Get default role permissions based on access level."""
        if access_level == AccessLevel.READ_ONLY:
            return {
                "view_data": True,
                "export_data": True,
                "generate_reports": False,
                "modify_data": False,
                "approve_changes": False,
                "manage_users": False,
            }

        elif access_level == AccessLevel.READ_WRITE or access_level == "analyst":
            return {
                "view_data": True,
                "export_data": True,
                "generate_reports": True,
                "modify_data": True,
                "create_analysis": True,
                "approve_changes": False,
                "manage_users": False,
            }

        elif access_level == AccessLevel.ADMIN or access_level == "manager":
            return {
                "view_data": True,
                "export_data": True,
                "generate_reports": True,
                "modify_data": True,
                "create_analysis": True,
                "approve_changes": True,
                "manage_team": True,
                "manage_users": False,
            }

        elif access_level == AccessLevel.SUPER_ADMIN:
            return {
                "view_data": True,
                "export_data": True,
                "generate_reports": True,
                "modify_data": True,
                "create_analysis": True,
                "approve_changes": True,
                "manage_team": True,
                "manage_users": True,
                "system_admin": True,
            }

        else:
            return self._get_default_role_permissions(AccessLevel.READ_ONLY)

    def _determine_role_type(self, access_level: str) -> str:
        """Determine role type based on access level."""
        if access_level == AccessLevel.READ_ONLY:
            return RoleType.VIEWER
        elif access_level == AccessLevel.READ_WRITE or access_level == "analyst":
            return RoleType.ANALYST
        elif access_level == AccessLevel.ADMIN or access_level == "manager":
            return RoleType.ENGAGEMENT_MANAGER
        elif access_level == AccessLevel.SUPER_ADMIN:
            return RoleType.PLATFORM_ADMIN
        else:
            return RoleType.VIEWER

    async def _log_access(
        self, user_id: str, action_type: str, result: str, reason: str = None, **kwargs
    ):
        """Log access events for audit trail."""
        if not self.is_available:
            return

        try:
            details = {}
            for key, value in kwargs.items():
                if key == "details" and isinstance(value, dict):
                    details.update(value)
                else:
                    details[key] = value

            audit_log = AccessAuditLog(
                user_id=user_id,
                action_type=action_type,
                result=result,
                reason=reason,
                details=details,
            )

            self.db.add(audit_log)
            await self.db.commit()

        except Exception as e:
            # Log warning instead of error - audit failure shouldn't block operations
            logger.warning(
                f"Failed to log access audit (table may not exist): {str(e)}"
            )
            await self.db.rollback()
            # Don't fail the main operation if logging fails
            pass

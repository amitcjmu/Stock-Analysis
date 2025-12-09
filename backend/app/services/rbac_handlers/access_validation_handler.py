"""
Access Validation Handler for RBAC operations.
Handles user access validation, permission checking, and authorization.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import and_, select

from .base_handler import BaseRBACHandler

# Import RBAC models with fallback
try:
    from app.models.rbac import (
        AccessLevel,
        ClientAccess,
        EngagementAccess,
        RoleType,
        UserProfile,
        UserRole,
        UserStatus,
    )

    RBAC_MODELS_AVAILABLE = True
except ImportError:
    RBAC_MODELS_AVAILABLE = False
    UserProfile = UserRole = ClientAccess = EngagementAccess = None
    UserStatus = AccessLevel = RoleType = None

# Import user and client models with fallback
try:
    from app.models.client_account import ClientAccount, Engagement

    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    ClientAccount = Engagement = None

logger = logging.getLogger(__name__)


class AccessValidationHandler(BaseRBACHandler):
    """Handler for access validation and permission checking."""

    async def validate_user_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str = None,
        action: str = "read",
    ) -> Dict[str, Any]:
        """Validate if user has access to a specific resource."""
        if not self.is_available:
            return {
                "status": "error",
                "message": "RBAC models not available",
                "has_access": False,
            }

        try:
            # First check if user exists and is active
            query = select(UserProfile).where(
                and_(
                    UserProfile.user_id == user_id,
                    UserProfile.status == UserStatus.ACTIVE,
                )
            )
            result = await self.db.execute(query)
            user_profile = result.scalar_one_or_none()

            if not user_profile:
                return {
                    "status": "error",
                    "message": "User not found or inactive",
                    "has_access": False,
                }

            # Route to specific validation based on resource type
            if resource_type == "client":
                has_access = await self._validate_client_access(
                    user_id, resource_id, action
                )
            elif resource_type == "engagement":
                has_access = await self._validate_engagement_access(
                    user_id, resource_id, action
                )
            elif resource_type == "admin":
                has_access = await self._validate_admin_access(user_id)
            else:
                has_access = await self._validate_default_access(user_id, action)

            # Log the access attempt
            await self._log_access(
                user_id=user_id,
                action_type=f"access_validation_{resource_type}",
                result="allowed" if has_access else "denied",
                reason=f"Access {action} on {resource_type} {resource_id}",
                details={
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "action": action,
                },
            )

            return {
                "status": "success",
                "has_access": has_access,
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
            }

        except Exception as e:
            logger.error(f"Error in validate_user_access: {e}")
            return {
                "status": "error",
                "message": f"Access validation failed: {str(e)}",
                "has_access": False,
            }

    async def _validate_client_access(
        self, user_id: str, client_id: str, action: str
    ) -> bool:
        """Validate access to a specific client."""
        try:
            query = select(ClientAccess).where(
                and_(
                    ClientAccess.user_profile_id == user_id,
                    ClientAccess.client_account_id == client_id,
                    ClientAccess.is_active == True,  # noqa: E712
                )
            )
            result = await self.db.execute(query)
            client_access = result.scalar_one_or_none()

            if not client_access:
                return False

            # Check if the action is allowed based on access level and permissions
            permissions = client_access.permissions or {}

            # Map actions to permission keys
            action_permission_map = {
                "read": ["view_assets", "view_reports", "view_engagement_overview"],
                "write": ["upload_data", "modify_settings", "create_analysis"],
                "delete": ["delete_data"],
                "admin": ["manage_users", "system_administration"],
            }

            required_permissions = action_permission_map.get(action, [])

            # Check if user has any of the required permissions
            for perm in required_permissions:
                if permissions.get(perm, False):
                    return True

            return False

        except Exception as e:
            logger.error(f"Error validating client access: {e}")
            return False

    async def _validate_engagement_access(
        self, user_id: str, engagement_id: str, action: str
    ) -> bool:
        """Validate access to a specific engagement."""
        try:
            query = select(EngagementAccess).where(
                and_(
                    EngagementAccess.user_profile_id == user_id,
                    EngagementAccess.engagement_id == engagement_id,
                    EngagementAccess.is_active == True,  # noqa: E712
                )
            )
            result = await self.db.execute(query)
            engagement_access = result.scalar_one_or_none()

            if not engagement_access:
                # Try to get access through client access
                engagement_query = select(Engagement).where(
                    Engagement.id == engagement_id
                )
                eng_result = await self.db.execute(engagement_query)
                engagement = eng_result.scalar_one_or_none()

                if engagement:
                    return await self._validate_client_access(
                        user_id, str(engagement.client_account_id), action
                    )
                return False

            # Check engagement-specific permissions
            permissions = engagement_access.permissions or {}

            action_permission_map = {
                "read": ["view_engagement", "view_migration_plans"],
                "write": ["modify_engagement", "create_migration_plans"],
                "delete": ["delete_engagement_data"],
                "admin": ["manage_engagement_users"],
            }

            required_permissions = action_permission_map.get(action, [])

            for perm in required_permissions:
                if permissions.get(perm, False):
                    return True

            return False

        except Exception as e:
            logger.error(f"Error validating engagement access: {e}")
            return False

    async def _validate_admin_access(self, user_id: str) -> bool:
        """Validate if user has admin access."""
        try:
            query = select(UserRole).where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_type == RoleType.PLATFORM_ADMIN,
                    UserRole.is_active == True,  # noqa: E712
                )
            )
            result = await self.db.execute(query)
            admin_role = result.scalar_one_or_none()

            return admin_role is not None

        except Exception as e:
            logger.error(f"Error validating admin access: {e}")
            return False

    async def _validate_default_access(self, user_id: str, action: str) -> bool:
        """Validate default access for general platform features."""
        try:
            # Get user's highest role
            query = (
                select(UserRole)
                .where(
                    and_(
                        UserRole.user_id == user_id,
                        UserRole.is_active == True,  # noqa: E712
                    )
                )
                .order_by(UserRole.created_at.desc())
            )
            result = await self.db.execute(query)
            user_role = result.scalar_one_or_none()

            if not user_role:
                return action == "read"  # Default to read-only for users without roles

            permissions = user_role.permissions or {}

            # Basic action mapping
            if action == "read":
                return permissions.get("view_data", True)
            elif action == "write":
                return permissions.get("modify_data", False)
            elif action == "delete":
                return permissions.get("manage_users", False)

            return False

        except Exception as e:
            logger.error(f"Error validating default access: {e}")
            return False

    async def grant_client_access(
        self, user_id: str, client_id: str, access_data: Dict[str, Any], granted_by: str
    ) -> Dict[str, Any]:
        """Grant client access to a user."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Check if access already exists
            existing_query = select(ClientAccess).where(
                and_(
                    ClientAccess.user_profile_id == user_id,
                    ClientAccess.client_account_id == client_id,
                )
            )
            existing_result = await self.db.execute(existing_query)
            existing_access = existing_result.scalar_one_or_none()

            if existing_access:
                # Update existing access
                existing_access.access_level = access_data.get(
                    "access_level", existing_access.access_level
                )
                existing_access.permissions = access_data.get(
                    "permissions", existing_access.permissions
                )
                existing_access.is_active = True
                existing_access.granted_by = granted_by
                existing_access.updated_at = datetime.utcnow()

                await self.db.commit()

                return {
                    "status": "success",
                    "message": "Client access updated successfully",
                    "access_id": str(existing_access.id),
                    "action": "updated",
                }
            else:
                # Create new access
                client_access = ClientAccess(
                    user_profile_id=user_id,
                    client_account_id=client_id,
                    access_level=access_data.get("access_level", AccessLevel.READ_ONLY),
                    permissions=access_data.get(
                        "permissions",
                        self._get_default_permissions(
                            access_data.get("access_level", AccessLevel.READ_ONLY)
                        ),
                    ),
                    granted_by=granted_by,
                    notes=access_data.get("notes", ""),
                    expiry_date=access_data.get("expiry_date"),
                )

                self.db.add(client_access)
                await self.db.commit()
                await self.db.refresh(client_access)

                # Log the access grant
                await self._log_access(
                    user_id=granted_by,
                    action_type="grant_client_access",
                    result="success",
                    reason=f"Granted client access to user {user_id}",
                    details={
                        "target_user": user_id,
                        "client_id": client_id,
                        "access_level": access_data.get("access_level"),
                    },
                )

                return {
                    "status": "success",
                    "message": "Client access granted successfully",
                    "access_id": str(client_access.id),
                    "action": "created",
                }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in grant_client_access: {e}")
            return {"status": "error", "message": f"Failed to grant access: {str(e)}"}

"""
Validation and helper methods for Enhanced RBAC Service.
"""

from typing import Any, Dict

from sqlalchemy import and_, select

from .base import (
    ClientAccount,
    DataScope,
    DeletedItemType,
    EnhancedUserProfile,
    RoleLevel,
    logger,
)


class RBACValidators:
    """Validation and helper methods for RBAC operations."""

    def _validate_scope_assignment(
        self,
        role_level: RoleLevel,
        data_scope: DataScope,
        scope_client_account_id: str = None,
        scope_engagement_id: str = None,
    ) -> Dict[str, Any]:
        """Validate that role and scope assignment is logical."""

        # Platform admins must have platform scope
        if role_level == RoleLevel.PLATFORM_ADMIN and data_scope != DataScope.PLATFORM:
            return {
                "status": "error",
                "message": "Platform admins must have platform data scope",
            }

        # Client admins must have client scope with client ID
        if role_level == RoleLevel.CLIENT_ADMIN:
            if data_scope != DataScope.CLIENT or not scope_client_account_id:
                return {
                    "status": "error",
                    "message": "Client admins must have client scope with client account ID",
                }

        # Engagement managers must have engagement scope with both IDs
        if role_level == RoleLevel.ENGAGEMENT_MANAGER:
            if (
                data_scope != DataScope.ENGAGEMENT
                or not scope_engagement_id
                or not scope_client_account_id
            ):
                return {
                    "status": "error",
                    "message": "Engagement managers must have engagement scope with both client and engagement IDs",
                }

        return {"status": "success"}

    async def _check_resource_access(
        self,
        user_profile: EnhancedUserProfile,
        resource_type: str,
        resource_id: str = None,
        client_account_id: str = None,
        engagement_id: str = None,
        action: str = "read",
    ) -> Dict[str, Any]:
        """Check if user can access specific resource based on their scope."""

        # Anonymous users can only access demo data
        if user_profile.role_level == RoleLevel.ANONYMOUS:
            if resource_type == "demo" or (
                client_account_id and await self._is_demo_client(client_account_id)
            ):
                return {"allowed": True, "reason": "Demo data access"}
            return {
                "allowed": False,
                "reason": "Anonymous users can only access demo data",
            }

        # Check client access if client_account_id provided
        if client_account_id:
            if not user_profile.can_access_client(client_account_id):
                return {"allowed": False, "reason": "No access to this client account"}

        # Check engagement access if engagement_id provided
        if engagement_id:
            if not user_profile.can_access_engagement(engagement_id, client_account_id):
                return {"allowed": False, "reason": "No access to this engagement"}

        # Check action-specific permissions
        if (
            action in ["create", "update", "delete"]
            and user_profile.role_level == RoleLevel.VIEWER
        ):
            return {"allowed": False, "reason": "Viewers have read-only access"}

        return {
            "allowed": True,
            "reason": f"Access granted based on {user_profile.role_level} role",
        }

    async def _can_user_delete_item(
        self,
        user_profile: EnhancedUserProfile,
        item_type: DeletedItemType,
        client_account_id: str = None,
        engagement_id: str = None,
    ) -> bool:
        """Check if user can delete items based on their role and scope."""

        # Platform admins can delete anything
        if user_profile.is_platform_admin:
            return True

        # Client admins can delete within their client scope
        if user_profile.is_client_admin and user_profile.data_scope == DataScope.CLIENT:
            if client_account_id and user_profile.can_access_client(client_account_id):
                return True

        # Engagement managers can delete within their engagement scope
        if (
            user_profile.is_engagement_manager
            and user_profile.data_scope == DataScope.ENGAGEMENT
        ):
            if engagement_id and user_profile.can_access_engagement(
                engagement_id, client_account_id
            ):
                return True

        return False

    async def _is_demo_client(self, client_account_id: str) -> bool:
        """Check if a client account is demo/mock data."""
        try:
            query = select(ClientAccount).where(  # SKIP_TENANT_CHECK
                and_(
                    ClientAccount.id == client_account_id,
                    ClientAccount.is_mock == True,  # noqa: E712
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception:
            return False

    async def _perform_item_soft_delete(self, item_type: DeletedItemType, item_id: str):
        """Perform the actual soft delete on the target item."""
        # This would implement the actual soft delete logic for each item type
        # For now, just log the action
        logger.info(f"Performing soft delete on {item_type} with ID {item_id}")

        # TODO: Implement actual soft delete for each model type
        # if item_type == DeletedItemType.CLIENT_ACCOUNT:
        #     # Update ClientAccount.is_active = False
        # elif item_type == DeletedItemType.ENGAGEMENT:
        #     # Update Engagement.is_active = False
        # etc.

    async def _restore_item_from_soft_delete(
        self, item_type: DeletedItemType, item_id: str
    ):
        """Restore an item from soft delete."""
        # This would implement the actual restore logic for each item type
        logger.info(f"Restoring {item_type} with ID {item_id} from soft delete")

        # TODO: Implement actual restore for each model type
